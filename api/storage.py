"""
storage.py — File-based JSON storage for the AskRoss Blog Image API (no database).

Layout:
  storage/
    sessions/
      {session_id}/
        session.json          — full session + manifest + sections metadata
        sections/
          {n}/
            background.png    — raw background image
            composited.png    — final composited image
    assets/
      pool.json               — metadata for reusable pool images
    prompts/
      templates.json          — saved prompt templates with ratings
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

STORAGE_DIR  = Path(__file__).parent / "storage"
SESSIONS_DIR = STORAGE_DIR / "sessions"
ASSETS_DIR   = STORAGE_DIR / "assets"
PROMPTS_DIR  = STORAGE_DIR / "prompts"


def _ensure_dirs():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / session_id / "session.json"


def _section_dir(session_id: str, section_index: int) -> Path:
    return SESSIONS_DIR / session_id / "sections" / str(section_index)


def _pool_path() -> Path:
    return ASSETS_DIR / "pool.json"


def _templates_path() -> Path:
    return PROMPTS_DIR / "templates.json"


def _read_json(path: Path) -> Any:
    """Read a JSON file. Returns None if the file does not exist."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    """Atomically write data to a JSON file, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def create_session(session_id: str, data: dict) -> None:
    """Write a new session JSON to disk. Raises if it already exists."""
    path = _session_path(session_id)
    if path.exists():
        raise FileExistsError(f"Session already exists: {session_id}")
    _write_json(path, data)


def get_session(session_id: str) -> Optional[dict]:
    """Return the full session dict, or None if not found."""
    return _read_json(_session_path(session_id))


def update_session(session_id: str, updates: dict) -> dict:
    """Shallow-merge updates into an existing session. Returns updated session."""
    data = get_session(session_id)
    if data is None:
        raise FileNotFoundError(f"Session not found: {session_id}")
    data.update(updates)
    _write_json(_session_path(session_id), data)
    return data


def list_sessions() -> list:
    """Return all sessions as a list of summary dicts (id, title, status, created_at)."""
    if not SESSIONS_DIR.exists():
        return []
    results = []
    for child in sorted(SESSIONS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if child.is_dir():
            data = _read_json(child / "session.json")
            if data:
                results.append({
                    "id":            data.get("id"),
                    "article_title": data.get("article_title", ""),
                    "status":        data.get("status", "pending"),
                    "is_selling_article": data.get("is_selling_article", False),
                    "created_at":    data.get("created_at", ""),
                    "updated_at":    data.get("updated_at", ""),
                    "section_count": len(data.get("sections", [])),
                })
    return results


def delete_session(session_id: str) -> None:
    """Delete a session directory and all its contents."""
    import shutil
    session_dir = SESSIONS_DIR / session_id
    if session_dir.exists():
        shutil.rmtree(session_dir)


# ---------------------------------------------------------------------------
# Sections (stored inside the session JSON for simplicity)
# ---------------------------------------------------------------------------

def get_section(session_id: str, section_index: int) -> Optional[dict]:
    """Return the section dict at position section_index (0-based) from session JSON."""
    session = get_session(session_id)
    if session is None:
        return None
    sections = session.get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        return None
    return sections[section_index]


def update_section(session_id: str, section_index: int, updates: dict) -> dict:
    """Merge updates into a section and persist the session. Returns updated section."""
    session = get_session(session_id)
    if session is None:
        raise FileNotFoundError(f"Session not found: {session_id}")
    sections = session.get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise IndexError(f"Section index {section_index} out of range for session {session_id}")
    sections[section_index].update(updates)
    session["sections"] = sections
    _write_json(_session_path(session_id), session)
    return sections[section_index]


def get_section_by_number(session_id: str, section_number: int) -> tuple[Optional[dict], int]:
    """Return (section_dict, index) for a section with the given section_number."""
    session = get_session(session_id)
    if session is None:
        return None, -1
    for i, sec in enumerate(session.get("sections", [])):
        if sec.get("section_number") == section_number:
            return sec, i
    return None, -1


# ---------------------------------------------------------------------------
# Pool assets
# ---------------------------------------------------------------------------

def list_assets() -> list:
    """Return all pool image asset metadata records."""
    data = _read_json(_pool_path())
    return data if isinstance(data, list) else []


def get_asset(asset_id: str) -> Optional[dict]:
    """Return a single asset by id, or None."""
    for asset in list_assets():
        if asset.get("id") == asset_id:
            return asset
    return None


def save_asset(asset: dict) -> None:
    """Append or upsert an asset record in pool.json."""
    assets = list_assets()
    for i, a in enumerate(assets):
        if a.get("id") == asset.get("id"):
            assets[i] = asset
            _write_json(_pool_path(), assets)
            return
    assets.append(asset)
    _write_json(_pool_path(), assets)


def delete_asset(asset_id: str) -> bool:
    """Remove an asset by id. Returns True if found and deleted."""
    assets = list_assets()
    new_assets = [a for a in assets if a.get("id") != asset_id]
    if len(new_assets) == len(assets):
        return False
    _write_json(_pool_path(), new_assets)
    return True


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

def list_templates(section_type: Optional[str] = None) -> list:
    """Return all templates, optionally filtered by section_type."""
    data = _read_json(_templates_path())
    templates = data if isinstance(data, list) else []
    if section_type:
        templates = [t for t in templates if t.get("section_type") == section_type]
    return templates


def get_template(template_id: str) -> Optional[dict]:
    for t in list_templates():
        if t.get("id") == template_id:
            return t
    return None


def save_template(template: dict) -> dict:
    """Upsert a template. Returns the saved template."""
    templates = list_templates()
    for i, t in enumerate(templates):
        if t.get("id") == template.get("id"):
            templates[i] = template
            _write_json(_templates_path(), templates)
            return template
    templates.append(template)
    _write_json(_templates_path(), templates)
    return template


def rate_template(template_id: str, rating: int) -> Optional[dict]:
    """Apply a +1 or -1 rating to a template. Returns updated template or None."""
    templates = list_templates()
    for i, t in enumerate(templates):
        if t.get("id") == template_id:
            t["rating_sum"]   = t.get("rating_sum", 0) + rating
            t["rating_count"] = t.get("rating_count", 0) + 1
            templates[i] = t
            _write_json(_templates_path(), templates)
            return t
    return None


def best_template(section_type: str) -> Optional[dict]:
    """Return the highest-rated template for a section type (min 1 rating)."""
    candidates = [
        t for t in list_templates(section_type)
        if t.get("rating_count", 0) > 0
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda t: t.get("rating_sum", 0) / max(t.get("rating_count", 1), 1))
