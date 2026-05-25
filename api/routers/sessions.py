"""
sessions.py — Session management router for the AskRoss Blog Image API.
"""

from __future__ import annotations

import asyncio
import glob as glob_mod
import json
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

from PIL import Image

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..models import ArticleSubmission, RegenRequest, SectionUpdate, SessionResponse
from ..pipeline import (
    PARENT,
    REF_DIR,
    HOME_FOR_SALE_POOL,
    FONT_ALEO,
    FONT_OPENSANS_BOLD,
    build_prompts_for_manifest,
    composite_section,
    create_zip_package,
    derive_theme_label,
    extract_manifest,
    fetch_pexels_random,
    generate_section_background,
    load_env,
    refine_prompt_with_ai,
)
from ..storage import (
    ASSETS_DIR,
    SESSIONS_DIR,
    create_session,
    delete_session,
    get_asset,
    get_section_by_number,
    get_session,
    list_sessions,
    save_asset,
    update_section,
    update_session,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _session_to_response(data: dict) -> dict:
    sections = []
    for sec in data.get("sections", []):
        s = dict(sec)
        # Compute URLs from stored relative paths if not already present
        if not s.get("composited_url") and s.get("composited_path"):
            s["composited_url"] = _section_url(s["composited_path"])
        if not s.get("background_url") and s.get("background_path"):
            s["background_url"] = _section_url(s["background_path"])
        sections.append(s)
    return {
        "id":                 data.get("id"),
        "article_title":      data.get("article_title", ""),
        "status":             data.get("status", "draft"),
        "manifest":           data.get("manifest"),
        "is_selling_article": data.get("is_selling_article", False),
        "created_at":         data.get("created_at", ""),
        "updated_at":         data.get("updated_at", ""),
        "sections":           sections,
        "section_count":      len(sections),
    }


def _build_sections_from_manifest(manifest: dict) -> list:
    """Build section records from manifest, pre-populating planned prompts."""
    # Build prompt plan first
    prompt_plan = {}
    try:
        for p in build_prompts_for_manifest(manifest):
            prompt_plan[p["section_number"]] = p
    except Exception:
        pass

    sections = []
    for sec in manifest.get("h2_sections", []):
        num = sec["section_number"]
        plan = prompt_plan.get(num, {})
        sections.append({
            "section_number":   num,
            "h2_text":          sec["text"],
            "filename":         sec["filename"],
            "is_bottom_line":   sec.get("is_bottom_line", False),
            "is_faq":           sec.get("is_faq", False),
            "prompt":           plan.get("prompt"),
            "search_term":      plan.get("search_term"),
            "custom_prompt":    None,   # user override before generation
            "source":           "pool" if sec.get("is_faq") else "gemini",
            "background_path":  None,
            "composited_path":  None,
            "force_position":   None,
            "rating":           0,
            "notes":            "",
            "status":           "pending",
            "cost_usd":         None,
            "generation_time_s": None,
        })
    return sections


def _rel_path(abs_path: Optional[str]) -> Optional[str]:
    if not abs_path:
        return None
    try:
        rel = Path(abs_path).relative_to(SESSIONS_DIR)
        return str(rel).replace("\\", "/")
    except ValueError:
        return abs_path


def _section_url(rel: Optional[str]) -> Optional[str]:
    return f"/files/sessions/{rel}" if rel else None


def _manifest_section(manifest: dict, sec_num: int, extra: Optional[dict] = None) -> dict:
    for s in manifest.get("h2_sections", []):
        if s["section_number"] == sec_num:
            merged = {**s}
            if extra:
                merged.update({k: v for k, v in extra.items() if v is not None})
            return merged
    return extra or {}


def _jstr(obj: dict) -> str:
    return json.dumps(obj)


# ---------------------------------------------------------------------------
# GET /sessions
# ---------------------------------------------------------------------------

@router.get("/")
async def list_all_sessions():
    raw = list_sessions()
    return [_session_to_response(s) for s in raw]


# ---------------------------------------------------------------------------
# POST /sessions — create from article text
# ---------------------------------------------------------------------------

@router.post("/", response_model=None)
async def create_new_session(body: ArticleSubmission):
    session_id = str(uuid.uuid4())
    now = _now_iso()

    try:
        manifest = extract_manifest(body.article_text, body.article_title)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse article: {e}")

    sections = _build_sections_from_manifest(manifest)

    session_data = {
        "id":                 session_id,
        "article_title":      manifest.get("title", "Untitled"),
        "article_text":       body.article_text,
        "status":             "draft",
        "manifest":           manifest,
        "is_selling_article": manifest.get("is_selling_article", False),
        "sections":           sections,
        "created_at":         now,
        "updated_at":         now,
    }

    try:
        create_session(session_id, session_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {e}")

    return _session_to_response(session_data)


# ---------------------------------------------------------------------------
# GET /sessions/{id}
# ---------------------------------------------------------------------------

@router.get("/{session_id}")
async def get_session_detail(session_id: str):
    data = get_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(data)


# ---------------------------------------------------------------------------
# DELETE /sessions/{id}
# ---------------------------------------------------------------------------

@router.delete("/{session_id}")
async def delete_session_endpoint(session_id: str):
    data = get_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(session_id)
    return {"deleted": session_id}


# ---------------------------------------------------------------------------
# GET /sessions/{id}/plan — return planned prompts for all sections
# ---------------------------------------------------------------------------

@router.get("/{session_id}/plan")
async def get_session_plan(session_id: str):
    """Return planned prompt/source for each section so the user can review/edit before generation."""
    data = get_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    sections = data.get("sections", [])
    plan = []
    for sec in sections:
        plan.append({
            "section_number": sec["section_number"],
            "h2_text":        sec["h2_text"],
            "is_bottom_line": sec.get("is_bottom_line", False),
            "is_faq":         sec.get("is_faq", False),
            "prompt":         sec.get("custom_prompt") or sec.get("prompt"),
            "search_term":    sec.get("search_term"),
            "source":         sec.get("source", "gemini"),
        })
    return plan


# ---------------------------------------------------------------------------
# POST /sessions/{id}/start — mark session as generating (client then opens SSE)
# ---------------------------------------------------------------------------

@router.post("/{session_id}/start")
async def start_generation(session_id: str):
    data = get_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")
    update_session(session_id, {"status": "generating", "updated_at": _now_iso()})
    data = get_session(session_id)
    return _session_to_response(data)


# ---------------------------------------------------------------------------
# GET /sessions/{id}/stream — SSE: runs full generation pipeline
# ---------------------------------------------------------------------------

@router.get("/{session_id}/stream")
async def stream_generation(session_id: str, source: str = "gemini"):
    data = get_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator() -> AsyncGenerator[dict, None]:
        load_env()
        api_key = os.environ.get("OPENROUTER_IMAGE_API_KEY", "")

        session_dir = SESSIONS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        update_session(session_id, {"status": "generating", "updated_at": _now_iso()})

        sections = data.get("sections", [])
        manifest = data.get("manifest", {})
        total = len(sections)
        errors = []
        total_cost = 0.0

        def _log(msg: str, level: str = "info"):
            return {
                "event": "message",
                "data": _jstr({"type": "log", "message": msg, "level": level, "ts": _now_ts()}),
            }

        pending = [s for s in sections if s.get("status") != "done" or not s.get("composited_path")]
        yield _log(f"Starting generation for {total} section(s) ({len(pending)} pending)…")

        for i, section in enumerate(sections):
            sec_num = section["section_number"]
            h2 = section.get("h2_text", "")

            # Skip already-completed sections (e.g. after a backend restart mid-run)
            if section.get("status") == "done" and section.get("composited_path"):
                comp_rel = section["composited_path"]
                bg_rel = section.get("background_path")
                yield _log(f"[{i+1}/{total}] Section {sec_num}: already done — skipping")
                yield {
                    "event": "message",
                    "data": _jstr({
                        "type":           "section_done",
                        "section_number": sec_num,
                        "composited_url": _section_url(comp_rel),
                        "background_url": _section_url(bg_rel),
                        "prompt":         section.get("prompt"),
                        "source":         section.get("source"),
                        "cost_usd":       section.get("cost_usd", 0),
                        "elapsed_s":      section.get("generation_time_s", 0),
                    }),
                }
                continue

            sec_source = section.get("source", source)
            custom_prompt = section.get("custom_prompt")

            yield {
                "event": "message",
                "data": _jstr({
                    "type":           "section_start",
                    "section_number": sec_num,
                    "h2_text":        h2,
                    "index":          i,
                    "total":          total,
                }),
            }
            yield _log(f"[{i+1}/{total}] Section {sec_num}: \"{h2[:60]}\"")

            try:
                # ── Background generation ──────────────────────────────────
                if section.get("is_faq"):
                    yield _log(f"  → FAQ section: using pool image (no generation)")
                elif section.get("is_bottom_line"):
                    yield _log(f"  → Bottom-line section: using pool/overlay")
                else:
                    yield _log(f"  → Generating background via {sec_source.upper()}…")

                t0 = asyncio.get_event_loop().time()

                bg_result = await generate_section_background(
                    section=_manifest_section(manifest, sec_num),
                    manifest=manifest,
                    api_key=api_key,
                    source=sec_source,
                    custom_prompt=custom_prompt,
                    session_dir=session_dir,
                )

                elapsed = round(asyncio.get_event_loop().time() - t0, 1)
                cost_usd = _estimate_cost(bg_result.get("source", sec_source), elapsed)
                total_cost += cost_usd

                bg_rel = _rel_path(bg_result["image_path"])
                update_section(session_id, i, {
                    "background_path":  bg_rel,
                    "prompt":           bg_result.get("prompt_used") or section.get("prompt"),
                    "source":           bg_result.get("source"),
                    "status":           "background_done",
                    "generation_time_s": elapsed,
                    "cost_usd":         cost_usd,
                })
                yield _log(f"  ✓ Background ready ({elapsed}s, ~${cost_usd:.4f})")

                # ── Composite ─────────────────────────────────────────────
                yield _log(f"  → Compositing…")
                fp = section.get("force_position") or _default_position(i, section)

                composited_path = await composite_section(
                    section=_manifest_section(manifest, sec_num, extra=section),
                    session_dir=session_dir,
                    force_position=fp,
                )
                comp_rel = _rel_path(composited_path)

                update_section(session_id, i, {
                    "composited_path": comp_rel,
                    "force_position":  fp,
                    "status":          "done",
                })

                yield _log(f"  ✓ Composited — section {sec_num} complete")
                yield {
                    "event": "message",
                    "data": _jstr({
                        "type":           "section_done",
                        "section_number": sec_num,
                        "composited_url": _section_url(comp_rel),
                        "background_url": _section_url(bg_rel),
                        "prompt":         bg_result.get("prompt_used"),
                        "source":         bg_result.get("source"),
                        "cost_usd":       cost_usd,
                        "elapsed_s":      elapsed,
                    }),
                }

            except Exception as e:
                error_msg = str(e)
                errors.append({"section_number": sec_num, "error": error_msg})
                update_section(session_id, i, {"status": "error", "error": error_msg})
                yield _log(f"  ✗ Section {sec_num} failed: {error_msg}", "error")
                yield {
                    "event": "message",
                    "data": _jstr({"type": "section_error", "section_number": sec_num, "error": error_msg}),
                }

        final_status = "reviewing"
        update_session(session_id, {"status": final_status, "updated_at": _now_iso()})

        summary = f"Done — {total - len(errors)}/{total} succeeded"
        if total_cost > 0:
            summary += f", total ~${total_cost:.4f}"
        yield _log(summary, "success" if not errors else "warn")

        yield {
            "event": "message",
            "data": _jstr({
                "type":        "all_done",
                "status":      final_status,
                "errors":      errors,
                "total":       total,
                "total_cost":  round(total_cost, 4),
            }),
        }

    return EventSourceResponse(event_generator())


def _default_position(section_index: int, section: dict) -> Optional[str]:
    """Alternating lower-left / center by 0-based index. Bottom-line and FAQ exempt."""
    if section.get("is_bottom_line") or section.get("is_faq"):
        return None
    return "lower-left" if section_index % 2 == 0 else "center"


def _estimate_cost(source: str, elapsed_s: float) -> float:
    """Rough cost estimate. Gemini Flash via OpenRouter ~$0.0003/image."""
    if source == "gemini":
        return 0.0003
    if source == "pexels":
        return 0.0
    return 0.0  # pool


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/prompt — save custom prompt before generation
# ---------------------------------------------------------------------------

@router.post("/{session_id}/sections/{section_number}/prompt")
async def set_section_prompt(session_id: str, section_number: int, body: dict):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")
    updates = {}
    if "prompt" in body:
        updates["custom_prompt"] = body["prompt"]
    if "source" in body:
        updates["source"] = body["source"]
    return update_section(session_id, idx, updates)


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/rate
# ---------------------------------------------------------------------------

@router.post("/{session_id}/sections/{section_number}/rate")
async def rate_section(session_id: str, section_number: int, body: dict):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")
    rating = body.get("rating", 0)
    return update_section(session_id, idx, {"rating": rating})


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/notes
# ---------------------------------------------------------------------------

@router.post("/{session_id}/sections/{section_number}/notes")
async def update_section_notes(session_id: str, section_number: int, body: dict):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")
    return update_section(session_id, idx, {"notes": body.get("notes", "")})


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/filename
# ---------------------------------------------------------------------------

@router.post("/{session_id}/sections/{section_number}/filename")
async def update_section_filename(session_id: str, section_number: int, body: dict):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")
    return update_section(session_id, idx, {"filename": body.get("filename", "")})


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/recomposite  (alias → composite)
# POST /sessions/{id}/sections/{n}/composite
# ---------------------------------------------------------------------------

async def _do_recomposite(session_id: str, section_number: int, body: dict):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    manifest = session.get("manifest", {})
    sec, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")
    if not sec.get("background_path"):
        raise HTTPException(status_code=422, detail="No background generated yet")

    session_dir = SESSIONS_DIR / session_id
    manifest_sec = _manifest_section(manifest, section_number, extra=sec)
    fp = body.get("position") or sec.get("force_position")

    try:
        composited_path = await composite_section(
            section=manifest_sec,
            session_dir=session_dir,
            force_position=fp,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compositing failed: {e}")

    comp_rel = _rel_path(composited_path)
    update_section(session_id, idx, {
        "composited_path": comp_rel,
        "force_position":  fp,
        "status":          "done",
    })
    return {
        "section_number": section_number,
        "composited_url": _section_url(comp_rel),
        "force_position": fp,
    }


@router.post("/{session_id}/sections/{section_number}/recomposite")
async def recomposite_section(session_id: str, section_number: int, body: dict = {}):
    return await _do_recomposite(session_id, section_number, body)


@router.post("/{session_id}/sections/{section_number}/composite")
async def composite_section_endpoint(session_id: str, section_number: int, body: dict = {}):
    return await _do_recomposite(session_id, section_number, body)


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/regen — regenerate background
# ---------------------------------------------------------------------------

@router.post("/{session_id}/sections/{section_number}/regen")
async def regen_section(session_id: str, section_number: int, body: RegenRequest):
    import shutil

    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    manifest = session.get("manifest", {})
    sec, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")

    load_env()
    api_key = os.environ.get("OPENROUTER_IMAGE_API_KEY", "")
    session_dir = SESSIONS_DIR / session_id
    manifest_sec = _manifest_section(manifest, section_number, extra=sec)

    # ── Specific pool image selected via asset library ─────────────────────────
    if body.source == "pool" and body.pool_image_id:
        asset = get_asset(body.pool_image_id)
        if asset is None:
            raise HTTPException(status_code=404, detail=f"Pool asset {body.pool_image_id} not found")

        asset_filename = asset.get("filename") or asset.get("source_name")
        if not asset_filename:
            raise HTTPException(status_code=422, detail="Pool asset has no filename")

        asset_file = ASSETS_DIR / "pool_images" / asset_filename
        if not asset_file.exists():
            raise HTTPException(status_code=404, detail=f"Pool asset file not found: {asset_filename}")

        sec_dir = session_dir / "sections" / str(section_number)
        sec_dir.mkdir(parents=True, exist_ok=True)
        bg_path = str(sec_dir / "background.png")
        shutil.copy2(str(asset_file), bg_path)

        bg_rel = _rel_path(bg_path)
        update_section(session_id, idx, {
            "background_path": bg_rel,
            "source":          "pool",
            "status":          "background_done",
            "composited_path": None,
        })

        comp_rel = None
        try:
            fp = sec.get("force_position") or _default_position(idx, sec)
            composited_path = await composite_section(
                section=manifest_sec,
                session_dir=session_dir,
                force_position=fp,
            )
            comp_rel = _rel_path(composited_path)
            update_section(session_id, idx, {"composited_path": comp_rel, "status": "done"})
        except Exception:
            pass

        return {
            "section_number": section_number,
            "background_url": _section_url(bg_rel),
            "composited_url": _section_url(comp_rel),
            "prompt":         None,
            "source":         "pool",
            "status":         "done",
        }

    # ── Standard generation (gemini / pexels / random pool) ───────────────────
    try:
        bg_result = await generate_section_background(
            section=manifest_sec,
            manifest=manifest,
            api_key=api_key,
            source=body.source or sec.get("source", "gemini"),
            custom_prompt=body.prompt,
            session_dir=session_dir,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Background generation failed: {e}")

    bg_rel = _rel_path(bg_result["image_path"])
    update_section(session_id, idx, {
        "background_path": bg_rel,
        "prompt":          bg_result.get("prompt_used"),
        "source":          bg_result.get("source"),
        "status":          "background_done",
        "composited_path": None,
    })

    comp_rel = None
    try:
        fp = sec.get("force_position") or _default_position(idx, sec)
        composited_path = await composite_section(
            section=manifest_sec,
            session_dir=session_dir,
            force_position=fp,
        )
        comp_rel = _rel_path(composited_path)
        update_section(session_id, idx, {"composited_path": comp_rel, "status": "done"})
    except Exception:
        pass

    return {
        "section_number": section_number,
        "background_url": _section_url(bg_rel),
        "composited_url": _section_url(comp_rel),
        "prompt":         bg_result.get("prompt_used"),
        "source":         bg_result.get("source"),
        "status":         "done",
    }


# ---------------------------------------------------------------------------
# POST /sessions/{id}/stop — cancel ongoing generation
# ---------------------------------------------------------------------------

@router.post("/{session_id}/stop")
async def stop_generation(session_id: str):
    data = get_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")
    update_session(session_id, {"status": "draft", "updated_at": _now_iso()})
    return {"stopped": True, "session_id": session_id}


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/refine-prompt — AI-refine prompt from notes
# ---------------------------------------------------------------------------

@router.post("/{session_id}/sections/{section_number}/refine-prompt")
async def refine_section_prompt(session_id: str, section_number: int, body: dict):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    sec, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")

    load_env()
    api_key = os.environ.get("OPENROUTER_IMAGE_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_IMAGE_API_KEY not set")

    current_prompt = body.get("current_prompt") or sec.get("prompt") or ""
    notes = body.get("notes", "")
    h2_text = sec.get("h2_text", "")

    # Persist the notes while we're at it
    if notes:
        update_section(session_id, idx, {"notes": notes})

    try:
        refined = await refine_prompt_with_ai(current_prompt, notes, h2_text, api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI refinement failed: {e}")

    return {"refined_prompt": refined, "section_number": section_number}


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/pexels-option — fetch Pexels alternative
# ---------------------------------------------------------------------------

@router.post("/{session_id}/sections/{section_number}/pexels-option")
async def get_pexels_option(session_id: str, section_number: int, body: dict = {}):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    manifest = session.get("manifest", {})
    sec, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")

    load_env()
    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    if not pexels_key:
        raise HTTPException(status_code=500, detail="PEXELS_API_KEY not set")

    search_term = (
        body.get("search_term")
        or sec.get("search_term")
        or sec.get("h2_text", "Canadian real estate")
    )

    session_dir = SESSIONS_DIR / session_id
    sec_dir = session_dir / "sections" / str(section_number)
    sec_dir.mkdir(parents=True, exist_ok=True)

    pexels_bg = str(sec_dir / "pexels_background.png")
    pexels_comp = str(sec_dir / "pexels_composited.png")

    try:
        exclude_url = sec.get("pexels_last_url")  # avoid re-fetching the same image
        img = await fetch_pexels_random(search_term, pexels_key, f"section {section_number}", exclude_url=exclude_url)
        img.save(pexels_bg, "PNG")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pexels fetch failed: {e}")

    try:
        manifest_sec = _manifest_section(manifest, section_number, extra=sec)
        fp = sec.get("force_position") or _default_position(idx, sec)
        composited_path = await composite_section(
            section=manifest_sec,
            session_dir=session_dir,
            force_position=fp,
            background_path=pexels_bg,
            out_filename="pexels_composited.png",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compositing failed: {e}")

    pexels_bg_rel = _rel_path(pexels_bg)
    pexels_comp_rel = _rel_path(pexels_comp)

    update_section(session_id, idx, {
        "pexels_composited_path": pexels_comp_rel,
        "pexels_background_path": pexels_bg_rel,
        "pexels_search_term": search_term,
    })

    return {
        "section_number": section_number,
        "pexels_composited_url": _section_url(pexels_comp_rel),
        "pexels_background_url": _section_url(pexels_bg_rel),
        "search_term": search_term,
    }


# ---------------------------------------------------------------------------
# POST /sessions/{id}/sections/{n}/save-to-pool — add image to asset pool
# ---------------------------------------------------------------------------

@router.post("/{session_id}/sections/{section_number}/save-to-pool")
async def save_section_to_pool(session_id: str, section_number: int, body: dict = {}):
    """Save a section background (NO text overlay) to the asset pool.

    body.image_type: "background" (default) | "pexels_bg"
    Always saves the raw background — never the composited version with text.
    """
    import shutil

    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    sec, idx = get_section_by_number(session_id, section_number)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")

    image_type = body.get("image_type", "background")
    category = body.get("category", "")

    if image_type == "pexels_bg":
        src_rel = sec.get("pexels_background_path")
        if not src_rel:
            raise HTTPException(status_code=422, detail="No Pexels background available for this section")
        abs_path = SESSIONS_DIR / src_rel
    else:
        # Default: save the raw AI/Pexels background (no text overlay)
        src_rel = sec.get("background_path")
        if not src_rel:
            raise HTTPException(status_code=422, detail="No background image available for this section")
        abs_path = SESSIONS_DIR / src_rel

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Background image file not found on disk")

    pool_dir = ASSETS_DIR / "pool_images"
    pool_dir.mkdir(parents=True, exist_ok=True)

    asset_id = str(uuid.uuid4())
    dest = pool_dir / f"{asset_id}.png"
    shutil.copy2(str(abs_path), str(dest))

    tags = body.get("tags") or (
        ["faq"] if sec.get("is_faq") else
        ["bottom-line"] if sec.get("is_bottom_line") else
        ["regular"]
    )

    asset = {
        "id":          asset_id,
        "name":        (sec.get("h2_text") or "")[:60],
        "source_name": dest.name,
        "filename":    dest.name,
        "url":         f"/files/assets/pool_images/{dest.name}",
        "tags":        tags,
        "category":    category,
        "usage_count": 0,
        "created_at":  _now_iso(),
    }
    save_asset(asset)

    return {"pool_image_id": asset_id, "url": asset["url"], "tags": tags, "image_type": image_type}


# ---------------------------------------------------------------------------
# GET /sessions/{id}/download
# ---------------------------------------------------------------------------

@router.get("/{session_id}/download")
async def download_session_images(session_id: str, approved_only: bool = False):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    sections = session.get("sections", [])
    to_package = [
        s for s in sections
        if (not approved_only or s.get("rating", 0) == 1)
        and (s.get("composited_path") or s.get("background_path"))
    ]

    if not to_package:
        raise HTTPException(status_code=422, detail="No images available to download")

    session_dir = SESSIONS_DIR / session_id
    try:
        zip_bytes = await asyncio.to_thread(create_zip_package, session_dir, to_package)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP: {e}")

    title_safe = session.get("article_title", "images")[:50].replace(" ", "_")
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="AskRoss_{title_safe}.zip"'},
    )


# ---------------------------------------------------------------------------
# Publication overlay / asset paths (mirrors run.py ASSET_PATHS)
# ---------------------------------------------------------------------------

_FEATURE_OVERLAY_2LINE  = str(REF_DIR / "BLOG POST - Feature Image" / "Feature image - Use this is title is two lines - overlay.png")
_FEATURE_OVERLAY_3LINE  = str(REF_DIR / "BLOG POST - Feature Image" / "Feature image - use this if title is three lines - overlay.png")
_DESKTOP_BANNER_OVERLAY = str(REF_DIR / "BLOG POST - Banner Images" / "Banner - Title of Article - Overlay.png")
_MOBILE_BANNER_OVERLAY  = str(REF_DIR / "BLOG POST - Banner Images" / "MOBILE - Title of Article - Overlay.png")
_GMB_OVERLAY_DIR        = str(REF_DIR / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE")


# ---------------------------------------------------------------------------
# GET /sessions/{id}/publication — return cached publication images
# ---------------------------------------------------------------------------

@router.get("/{session_id}/publication")
async def get_publication_images(session_id: str):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    pub = session.get("publication")
    if not pub:
        return {
            "feature_url": None,
            "banner_desktop_url": None,
            "banner_mobile_url": None,
            "gmb_urls": [],
            "feature_bg_url": None,
            "feature_prompt": None,
        }
    return pub


# ---------------------------------------------------------------------------
# POST /sessions/{id}/publication — generate feature / banner / mobile / GMB
# ---------------------------------------------------------------------------

@router.post("/{session_id}/publication")
async def generate_publication_images(session_id: str):
    """Generate feature image, desktop banner, mobile image, and GMB images for a session."""
    from src.compositors.shared import sanitize_filename

    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    load_env()
    api_key = os.environ.get("OPENROUTER_IMAGE_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_IMAGE_API_KEY not set")

    title      = session.get("article_title", "")
    is_selling = session.get("is_selling_article", False)
    manifest   = session.get("manifest", {})

    pub_dir = SESSIONS_DIR / session_id / "publication"
    pub_dir.mkdir(parents=True, exist_ok=True)


    def _rel(path: str) -> str:
        return str(Path(path).relative_to(SESSIONS_DIR)).replace("\\", "/")

    def _url(rel: str) -> str:
        return f"/files/sessions/{rel}"

    # ── 1. Generate feature background ────────────────────────────────────────
    try:
        from generate_gemini import _prompt_for_feature, _generate_image, _is_selling_article as _gemini_is_selling
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Cannot import pipeline: {e}")

    feature_bg_path = str(pub_dir / "feature_bg.png")
    feature_prompt_used = ""

    if is_selling or _gemini_is_selling(title):
        pool_files = glob_mod.glob(HOME_FOR_SALE_POOL)
        if not pool_files:
            raise HTTPException(status_code=500, detail="No home-for-sale pool images found")
        chosen = random.choice(pool_files)
        feature_bg_img = Image.open(chosen).convert("RGB")
        feature_bg_img.save(feature_bg_path, "PNG")
        feature_prompt_used = "home-for-sale pool"
    else:
        theme_label    = derive_theme_label(manifest)
        feature_prompt = _prompt_for_feature(title, theme_label)

        if feature_prompt is None:
            # selling article caught by _prompt_for_feature — use pool
            pool_files = glob_mod.glob(HOME_FOR_SALE_POOL)
            if not pool_files:
                raise HTTPException(status_code=500, detail="No home-for-sale pool images found")
            chosen = random.choice(pool_files)
            feature_bg_img = Image.open(chosen).convert("RGB")
            feature_bg_img.save(feature_bg_path, "PNG")
            feature_prompt_used = "pool fallback"
        else:
            feature_bg_img = await asyncio.to_thread(_generate_image, feature_prompt, api_key, "feature background")
            if feature_bg_img is None:
                raise HTTPException(
                    status_code=500,
                    detail="Feature background generation failed (filtered by model)",
                )
            feature_bg_img.save(feature_bg_path, "PNG")
            feature_prompt_used = feature_prompt[:120]

    import shutil as _shutil

    # Use a temp subdir for compositor output (may have special chars in names)
    tmp_dir = str(pub_dir / "_tmp")
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)
    safe_title = sanitize_filename(title)

    # ── 2. Compose feature image (700x450) ───────────────────────────────────
    try:
        from src.compositors.compose_feature import compose_feature_image
        feature_results = await asyncio.to_thread(
            compose_feature_image,
            title,
            derive_theme_label(manifest),
            feature_bg_img,
            _FEATURE_OVERLAY_2LINE,
            _FEATURE_OVERLAY_3LINE,
            FONT_ALEO,
            FONT_OPENSANS_BOLD,
            tmp_dir,
            safe_title,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature image compositing failed: {e}")

    # Copy compositor output to fixed clean names (safe for HTTP serving)
    feature_compositor_path = feature_results[1][0] if len(feature_results) >= 2 else None
    feature_out_path = str(pub_dir / "feature.png")
    if feature_compositor_path and Path(feature_compositor_path).exists():
        _shutil.copy2(feature_compositor_path, feature_out_path)

    # ── 3. Compose banners (1286x300 desktop + 400x600 mobile) ──────────────
    try:
        from src.compositors.compose_banners import compose_all_banners
        banner_results = await asyncio.to_thread(
            compose_all_banners,
            feature_bg_img,
            _DESKTOP_BANNER_OVERLAY,
            _MOBILE_BANNER_OVERLAY,
            tmp_dir,
            safe_title,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Banner compositing failed: {e}")

    desktop_compositor_path = banner_results[0][0] if len(banner_results) >= 1 else None
    mobile_compositor_path  = banner_results[1][0] if len(banner_results) >= 2 else None
    desktop_out_path = str(pub_dir / "banner_desktop.png")
    mobile_out_path  = str(pub_dir / "banner_mobile.png")
    if desktop_compositor_path and Path(desktop_compositor_path).exists():
        _shutil.copy2(desktop_compositor_path, desktop_out_path)
    if mobile_compositor_path and Path(mobile_compositor_path).exists():
        _shutil.copy2(mobile_compositor_path, mobile_out_path)

    # ── 4. Compose GMB images (1200x900 × 4 cities) ──────────────────────────
    gmb_tmp_dir = str(pub_dir / "_tmp_gmb")
    Path(gmb_tmp_dir).mkdir(parents=True, exist_ok=True)
    gmb_out_dir = str(pub_dir / "gmb")
    Path(gmb_out_dir).mkdir(parents=True, exist_ok=True)
    gmb_urls: list = []
    try:
        from src.compositors.compose_gmb import compose_all_gmb_images
        gmb_results = await asyncio.to_thread(
            compose_all_gmb_images,
            title,
            feature_bg_img,
            _GMB_OVERLAY_DIR,
            FONT_OPENSANS_BOLD,
            gmb_tmp_dir,
            safe_title,
        )
        if isinstance(gmb_results, list):
            for i, (path, ok) in enumerate(gmb_results):
                if Path(path).exists():
                    # Extract city name from compositor filename prefix (e.g. "Toronto - ...")
                    city_slug = Path(path).stem.split(" - ")[0].strip().lower().replace(" ", "_")
                    dest = pub_dir / "gmb" / f"{city_slug}.png"
                    _shutil.copy2(path, str(dest))
                    gmb_urls.append(_url(_rel(str(dest))))
    except Exception as e:
        # GMB failure is non-fatal
        print(f"[WARNING] GMB compositing failed: {e}")

    # ── 5. Build response ─────────────────────────────────────────────────────
    result = {
        "feature_bg_url":     _url(_rel(feature_bg_path))  if Path(feature_bg_path).exists() else None,
        "feature_url":        _url(_rel(feature_out_path))  if Path(feature_out_path).exists() else None,
        "banner_desktop_url": _url(_rel(desktop_out_path))  if Path(desktop_out_path).exists() else None,
        "banner_mobile_url":  _url(_rel(mobile_out_path))   if Path(mobile_out_path).exists() else None,
        "gmb_urls":           gmb_urls,
        "feature_prompt":     feature_prompt_used,
    }

    # Persist publication URLs into session record
    update_session(session_id, {"publication": result, "updated_at": _now_iso()})

    return result


# ---------------------------------------------------------------------------
# POST /sessions/{id}/publication/recomposite — re-render with custom text
# ---------------------------------------------------------------------------

@router.post("/{session_id}/publication/recomposite")
async def recomposite_publication(session_id: str, body: dict = {}):
    """Re-composite publication images using an existing feature background but with
    custom theme label and/or article title text. Does NOT re-generate the background."""
    import shutil as _shutil
    from src.compositors.shared import sanitize_filename

    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    pub_data = session.get("publication") or {}
    pub_dir = SESSIONS_DIR / session_id / "publication"

    # The raw background must already exist
    feature_bg_path = str(pub_dir / "feature_bg.png")
    if not Path(feature_bg_path).exists():
        raise HTTPException(status_code=422, detail="No feature background yet — run Generate All first")

    manifest   = session.get("manifest", {})
    orig_title = session.get("article_title", "")

    custom_theme = body.get("theme") or derive_theme_label(manifest)
    custom_title = body.get("title") or orig_title

    feature_bg_img = Image.open(feature_bg_path).convert("RGB")
    safe_title = sanitize_filename(custom_title)

    tmp_dir = str(pub_dir / "_tmp")
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)

    def _rel(path: str) -> str:
        return str(Path(path).relative_to(SESSIONS_DIR)).replace("\\", "/")
    def _url(rel: str) -> str:
        return f"/files/sessions/{rel}"

    # ── Feature image ────────────────────────────────────────────────────────
    try:
        from src.compositors.compose_feature import compose_feature_image
        feature_results = await asyncio.to_thread(
            compose_feature_image,
            custom_title,
            custom_theme,
            feature_bg_img,
            _FEATURE_OVERLAY_2LINE,
            _FEATURE_OVERLAY_3LINE,
            FONT_ALEO,
            FONT_OPENSANS_BOLD,
            tmp_dir,
            safe_title,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature compositing failed: {e}")

    feature_compositor_path = feature_results[1][0] if len(feature_results) >= 2 else None
    feature_out_path = str(pub_dir / "feature.png")
    if feature_compositor_path and Path(feature_compositor_path).exists():
        _shutil.copy2(feature_compositor_path, feature_out_path)

    # ── Banners ──────────────────────────────────────────────────────────────
    try:
        from src.compositors.compose_banners import compose_all_banners
        banner_results = await asyncio.to_thread(
            compose_all_banners,
            feature_bg_img,
            _DESKTOP_BANNER_OVERLAY,
            _MOBILE_BANNER_OVERLAY,
            tmp_dir,
            safe_title,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Banner compositing failed: {e}")

    desktop_compositor_path = banner_results[0][0] if len(banner_results) >= 1 else None
    mobile_compositor_path  = banner_results[1][0] if len(banner_results) >= 2 else None
    desktop_out_path = str(pub_dir / "banner_desktop.png")
    mobile_out_path  = str(pub_dir / "banner_mobile.png")
    if desktop_compositor_path and Path(desktop_compositor_path).exists():
        _shutil.copy2(desktop_compositor_path, desktop_out_path)
    if mobile_compositor_path and Path(mobile_compositor_path).exists():
        _shutil.copy2(mobile_compositor_path, mobile_out_path)

    # ── GMB ──────────────────────────────────────────────────────────────────
    gmb_tmp_dir = str(pub_dir / "_tmp_gmb")
    Path(gmb_tmp_dir).mkdir(parents=True, exist_ok=True)
    gmb_out_dir = str(pub_dir / "gmb")
    Path(gmb_out_dir).mkdir(parents=True, exist_ok=True)
    gmb_urls: list = []
    try:
        from src.compositors.compose_gmb import compose_all_gmb_images
        gmb_results = await asyncio.to_thread(
            compose_all_gmb_images,
            custom_title,
            feature_bg_img,
            _GMB_OVERLAY_DIR,
            FONT_OPENSANS_BOLD,
            gmb_tmp_dir,
            safe_title,
        )
        if isinstance(gmb_results, list):
            for path, ok in gmb_results:
                if Path(path).exists():
                    city_slug = Path(path).stem.split(" - ")[0].strip().lower().replace(" ", "_")
                    dest = pub_dir / "gmb" / f"{city_slug}.png"
                    _shutil.copy2(path, str(dest))
                    gmb_urls.append(_url(_rel(str(dest))))
    except Exception as e:
        print(f"[WARNING] GMB recomposite failed: {e}")

    result = {
        "feature_bg_url":     pub_data.get("feature_bg_url"),
        "feature_url":        _url(_rel(feature_out_path))  if Path(feature_out_path).exists() else None,
        "banner_desktop_url": _url(_rel(desktop_out_path))  if Path(desktop_out_path).exists() else None,
        "banner_mobile_url":  _url(_rel(mobile_out_path))   if Path(mobile_out_path).exists() else None,
        "gmb_urls":           gmb_urls or pub_data.get("gmb_urls", []),
        "feature_prompt":     pub_data.get("feature_prompt"),
        "custom_theme":       custom_theme,
        "custom_title":       custom_title,
    }
    update_session(session_id, {"publication": result, "updated_at": _now_iso()})
    return result
