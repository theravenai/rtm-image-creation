"""
pipeline.py — FastAPI service wrapper around the AskRoss.ca image compositing pipeline.

Exposes async helpers that call into the parent directory's existing Python scripts
so the REST layer stays thin and all compositing logic lives in the original modules.
"""

from __future__ import annotations

import asyncio
import glob as glob_mod
import io
import os
import random
import re
import sys
import zipfile
from pathlib import Path
from typing import Optional

from PIL import Image

# ---------------------------------------------------------------------------
# Path bootstrap — add parent to sys.path so we can import the existing scripts
# ---------------------------------------------------------------------------

PARENT = Path(__file__).parent.parent.resolve()
API_DIR = Path(__file__).parent.resolve()

if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

REF_DIR = PARENT / "references"

# ---------------------------------------------------------------------------
# Asset paths (mirrors generate_gemini.py / generate_phase2.py)
# ---------------------------------------------------------------------------

ARTICLE_OVERLAY      = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "(1) AskRoss.ca - Just logo and grey overlay.png")
BOTTOM_LINE_OVERLAY  = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "(8) Rule - AskRoss.ca - For The Closer - No Overlay - Just Logo.png")
BOTTOM_LINE_POOL     = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "Reusable Image Large Article Image Assets" / "AskRoss.ca - Bottom line or Advice from Ross Taylor Mortgages*.png")
FAQ_POOL             = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "Reusable Image Large Article Image Assets" / "AskRoss.ca - All of the FAQs in this article*.png")
HOME_FOR_SALE_POOL   = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "Reusable Image Large Article Image Assets" / "home for sale options" / "*.png")
FONT_ARCHIVO         = str(REF_DIR / "(2) Newsletter Image Creation - Use for process creation reference" / "(1) Banner Images" / "fonts" / "Archivo_Black" / "ArchivoBlack-Regular.ttf")
FONT_ALEO            = str(PARENT / "fonts" / "Aleo" / "static" / "Aleo-Bold.ttf")
FONT_OPENSANS_BOLD   = str(PARENT / "fonts" / "Open_Sans" / "static" / "OpenSans-Bold.ttf")


# ---------------------------------------------------------------------------
# env loader (reuses generate_gemini._load_env)
# ---------------------------------------------------------------------------

def load_env():
    """Load .env from parent directory (same logic as generate_gemini._load_env)."""
    try:
        from generate_gemini import _load_env
        _load_env()
    except ImportError:
        from dotenv import load_dotenv
        local = PARENT / ".env"
        fallback = REF_DIR / "(2) Newsletter Image Creation - Use for process creation reference" / ".env"
        if local.exists():
            load_dotenv(local)
        elif fallback.exists():
            load_dotenv(fallback)


# ---------------------------------------------------------------------------
# Theme label derivation (reuses run._derive_theme_label)
# ---------------------------------------------------------------------------

def derive_theme_label(manifest: dict) -> str:
    try:
        from run import _derive_theme_label
        return _derive_theme_label(manifest)
    except ImportError:
        # Inline fallback
        if manifest.get("theme_label"):
            return manifest["theme_label"]
        title = manifest.get("title", "").lower()
        if any(k in title for k in ("bank of canada", "interest rate", "rate cut", "rate hike")):
            return "Mortgage Rates"
        if any(k in title for k in ("renew", "renewal", "payment shock")):
            return "Renewal Tips"
        if any(k in title for k in ("refinanc", "heloc", "equity")):
            return "Refinancing"
        if any(k in title for k in ("buy", "buyer", "first-time", "purchase")):
            return "Buyer's Guide"
        if any(k in title for k in ("credit", "debt", "financial reset", "budget")):
            return "Financial Advice"
        if any(k in title for k in ("market", "home price", "recovery", "crash")):
            return "Market Update"
        return "Housing News"


# ---------------------------------------------------------------------------
# Manifest extraction from raw article text
# ---------------------------------------------------------------------------

def _sanitize_filename(text: str, index: int) -> str:
    text = text.rstrip("?!")
    text = text.replace(": ", "_ ")
    text = text.replace(":", "_")
    for ch in '"*\\/<>|':
        text = text.replace(ch, "")
    text = text.strip()
    return f"AskRoss.ca - {index} - {text}.png"


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def _count_title_lines(title: str) -> int:
    import math
    chars_per_line = 48
    line_count = math.ceil(len(title) / chars_per_line)
    return 3 if line_count >= 3 else 2


def _is_selling_article(title: str) -> bool:
    low = title.lower()
    return any(kw in low for kw in ("sell", "selling", "for sale"))


def extract_manifest(article_text: str, article_title: Optional[str] = None) -> dict:
    """Parse article text to extract H2 headings and build a manifest dict.

    Supports both Markdown (##) headings and plain text.
    If article_title is not given, falls back to the first # heading.
    """
    lines = article_text.splitlines()

    # --- Extract title ---
    title = article_title or ""
    if not title:
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                title = re.sub(r"^\*\*|\*\*$", "", stripped[2:].strip()).strip()
                break
    if not title:
        title = "Untitled Article"

    # --- Find "Jump to a specific section" line ---
    jump_idx = None
    for i, line in enumerate(lines):
        if re.search(r"jump to a specific section", line, re.IGNORECASE):
            jump_idx = i
            break

    # Use all lines after jump marker, or all lines if no jump marker
    body_lines = lines[jump_idx + 1:] if jump_idx is not None else lines

    # --- Collect ## H2 headings ---
    h2_sections = []
    section_counter = 2
    image_index = 1

    for line in body_lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            raw_h2 = stripped[3:].strip()
            h2_text = re.sub(r"^\*\*|\*\*$", "", raw_h2).strip()

            # Stop at metadata section
            if re.search(r"metadata elements", h2_text, re.IGNORECASE):
                break

            is_bottom_line = bool(
                re.search(r"bottom line", h2_text, re.IGNORECASE)
                or re.search(r"advice from ross", h2_text, re.IGNORECASE)
            )
            is_faq = bool(
                re.search(r"\bfaq\b", h2_text, re.IGNORECASE)
                or re.search(r"list of all faqs", h2_text, re.IGNORECASE)
                or re.search(r"frequently asked", h2_text, re.IGNORECASE)
            )

            h2_sections.append({
                "text": h2_text,
                "section_number": section_counter,
                "filename": _sanitize_filename(h2_text, index=image_index),
                "is_bottom_line": is_bottom_line,
                "is_faq": is_faq,
                "prompt_hint": _generate_prompt_hint(h2_text),
            })
            section_counter += 1
            image_index += 1

    # Detect selling article
    is_selling = _is_selling_article(title)

    # Auto-assign theme_label
    theme_label = _auto_theme_label(title)

    manifest = {
        "title": title,
        "slug": _slugify(title),
        "title_line_count": _count_title_lines(title),
        "gmb_locations": ["Toronto", "Ottawa", "Richmond Hill", "Mississauga"],
        "h2_sections": h2_sections,
        "theme_label": theme_label,
        "is_selling_article": is_selling,
    }
    return manifest


def _auto_theme_label(title: str) -> str:
    low = title.lower()
    if any(k in low for k in ("bank of canada", "interest rate", "rate cut", "rate hike")):
        return "Mortgage Rates"
    if any(k in low for k in ("renew", "renewal", "payment shock")):
        return "Renewal Tips"
    if any(k in low for k in ("refinanc", "heloc", "equity")):
        return "Refinancing"
    if any(k in low for k in ("buy", "buyer", "first-time", "purchase")):
        return "Buyer's Guide"
    if any(k in low for k in ("credit", "debt", "financial reset", "budget")):
        return "Financial Advice"
    if any(k in low for k in ("market", "home price", "recovery", "crash")):
        return "Market Update"
    return "Housing News"


def _generate_prompt_hint(h2_text: str) -> str:
    """Lightweight prompt hint generator (mirrors parse_article.generate_prompt_hint)."""
    try:
        from src.parser.parse_article import generate_prompt_hint
        return generate_prompt_hint(h2_text)
    except ImportError:
        return (
            f"A photorealistic Canadian homeowner scene illustrating '{h2_text}', "
            "professional lighting, suburban or urban Toronto setting."
        )


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_prompts_for_manifest(manifest: dict) -> list:
    """Return list of {section_number, filename, prompt, search_term, source} dicts."""
    results = []

    try:
        from generate_gemini import _prompt_for_section, _prompt_for_bottom_line, _prompt_for_feature
        from generate_phase2 import _pexels_query_for_section, _pexels_query_for_feature, _pexels_query_for_bottom_line
    except ImportError as e:
        print(f"Warning: could not import prompt builders from parent scripts: {e}")
        from generate_gemini import _prompt_for_section, _prompt_for_bottom_line, _prompt_for_feature
        _pexels_query_for_section = lambda s: "Canadian home real estate"
        _pexels_query_for_feature = lambda t: "Canadian neighbourhood homes street"
        _pexels_query_for_bottom_line = lambda m: "mortgage advisor professional office"

    for section in manifest.get("h2_sections", []):
        if section.get("is_faq"):
            gemini_prompt = None
            pexels_query = None
        elif section.get("is_bottom_line"):
            gemini_prompt = _prompt_for_bottom_line(manifest)
            pexels_query = _pexels_query_for_bottom_line(manifest)
        else:
            gemini_prompt = _prompt_for_section(section)
            pexels_query = _pexels_query_for_section(section)

        results.append({
            "section_number": section["section_number"],
            "filename":       section["filename"],
            "prompt":         gemini_prompt,
            "search_term":    pexels_query,
            "source":         "gemini",
        })

    return results


# ---------------------------------------------------------------------------
# Background generation (per section)
# ---------------------------------------------------------------------------

async def generate_section_background(
    section: dict,
    manifest: dict,
    api_key: str,
    source: str = "gemini",
    custom_prompt: Optional[str] = None,
    session_dir: Optional[Path] = None,
) -> dict:
    """Generate background for one section. Returns {image_path, prompt_used, source}.

    source: 'gemini' | 'pexels' | 'pool'
    - gemini: calls _generate_image from generate_gemini.py
    - pexels: calls _fetch_pexels from generate_phase2.py
    - pool:   picks a random pool image
    - is_faq: always picks from FAQ pool
    - is_bottom_line on selling article: picks from home for sale pool
    """
    sec_num = section.get("section_number", 0)
    out_dir = (session_dir / "sections" / str(sec_num)) if session_dir else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)
    bg_path = str(out_dir / "background.png")

    # --- FAQ: always pool ---
    if section.get("is_faq"):
        pool_files = glob_mod.glob(FAQ_POOL)
        if not pool_files:
            raise FileNotFoundError(f"No FAQ pool images found: {FAQ_POOL}")
        chosen = random.choice(pool_files)
        img = Image.open(chosen).convert("RGB")
        img.save(bg_path, "PNG")
        return {"image_path": bg_path, "prompt_used": None, "source": "pool", "pool_file": chosen}

    # --- Selling article bottom-line: home for sale pool ---
    is_selling = manifest.get("is_selling_article", False) or _is_selling_article(manifest.get("title", ""))
    if section.get("is_bottom_line") and is_selling:
        pool_files = glob_mod.glob(HOME_FOR_SALE_POOL)
        if not pool_files:
            raise FileNotFoundError(f"No home-for-sale pool images: {HOME_FOR_SALE_POOL}")
        chosen = random.choice(pool_files)
        img = Image.open(chosen).convert("RGB")
        img.save(bg_path, "PNG")
        return {"image_path": bg_path, "prompt_used": None, "source": "pool", "pool_file": chosen}

    # --- Pool override ---
    if source == "pool":
        pool_files = glob_mod.glob(HOME_FOR_SALE_POOL)
        if not pool_files:
            raise FileNotFoundError(f"No pool images found: {HOME_FOR_SALE_POOL}")
        chosen = random.choice(pool_files)
        img = Image.open(chosen).convert("RGB")
        img.save(bg_path, "PNG")
        return {"image_path": bg_path, "prompt_used": None, "source": "pool", "pool_file": chosen}

    # --- Build the prompt ---
    if custom_prompt:
        prompt_used = custom_prompt
    else:
        try:
            from generate_gemini import _prompt_for_section, _prompt_for_bottom_line
            if section.get("is_bottom_line"):
                prompt_used = _prompt_for_bottom_line(manifest)
            else:
                prompt_used = _prompt_for_section(section)
        except ImportError:
            prompt_used = section.get("prompt_hint", "Canadian home real estate")

    # --- Pexels ---
    if source == "pexels":
        pexels_key = os.environ.get("PEXELS_API_KEY", "")
        if not pexels_key:
            raise EnvironmentError("PEXELS_API_KEY not set")

        try:
            from generate_phase2 import _fetch_pexels, _pexels_query_for_section, _pexels_query_for_bottom_line
        except ImportError as e:
            raise ImportError(f"Cannot import Pexels helpers: {e}")

        if custom_prompt:
            query = custom_prompt
        elif section.get("is_bottom_line"):
            query = _pexels_query_for_bottom_line(manifest) or "mortgage advisor professional office"
        else:
            query = _pexels_query_for_section(section)

        img = await asyncio.to_thread(_fetch_pexels, query, pexels_key, f"section {sec_num}")
        img.save(bg_path, "PNG")
        return {"image_path": bg_path, "prompt_used": query, "source": "pexels"}

    # --- Gemini (default) ---
    gemini_key = api_key or os.environ.get("OPENROUTER_IMAGE_API_KEY", "")
    if not gemini_key:
        raise EnvironmentError("OPENROUTER_IMAGE_API_KEY not set")

    try:
        from generate_gemini import _generate_image
    except ImportError as e:
        raise ImportError(f"Cannot import Gemini helpers: {e}")

    img = await asyncio.to_thread(_generate_image, prompt_used, gemini_key, f"section {sec_num}")
    if img is None:
        # All prompts filtered — fall back to a pool image
        pool_files = glob_mod.glob(HOME_FOR_SALE_POOL)
        if pool_files:
            chosen = random.choice(pool_files)
            img = Image.open(chosen).convert("RGB")
            img.save(bg_path, "PNG")
            return {"image_path": bg_path, "prompt_used": prompt_used, "source": "pool_fallback", "pool_file": chosen}
        raise RuntimeError(f"Gemini returned no image for section {sec_num} and no pool fallback found")

    img.save(bg_path, "PNG")
    return {"image_path": bg_path, "prompt_used": prompt_used, "source": "gemini"}


# ---------------------------------------------------------------------------
# Compositing (per section)
# ---------------------------------------------------------------------------

async def refine_prompt_with_ai(
    current_prompt: str,
    notes: str,
    h2_text: str,
    api_key: str,
) -> str:
    """Call OpenRouter text API to rewrite an image prompt based on user feedback."""
    import requests

    # Use a text-capable model (NOT the image model)
    TEXT_MODEL = os.environ.get("OPENROUTER_TEXT_MODEL", "google/gemini-2.0-flash-001")

    system = (
        "You are an expert at writing Gemini image generation prompts for AskRoss.ca, "
        "a Canadian mortgage and real estate advice website. "
        "Prompts must describe a photorealistic, Canadian-context scene that visually illustrates the concept. "
        "Return only the improved prompt text — no preamble, no quotes, no explanation. Max 150 words."
    )
    combined = (
        f"Section heading: {h2_text}\n\n"
        f"Current prompt:\n{current_prompt}\n\n"
        f"User feedback on the generated image:\n{notes}\n\n"
        "Write an improved image generation prompt based on this feedback."
    )

    def _call():
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": TEXT_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": combined},
                ],
                "max_tokens": 300,
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if not content:
            raise RuntimeError(f"Empty response from model {TEXT_MODEL}: {data}")
        return content.strip()

    return await asyncio.to_thread(_call)


async def fetch_pexels_random(
    query: str,
    pexels_key: str,
    label: str,
    exclude_url: Optional[str] = None,
) -> "Image.Image":
    """Fetch a random landscape photo from Pexels — avoids returning the same image twice."""
    import requests as req_mod

    PEXELS_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }

    def _call():
        # Fetch a larger pool and randomize
        page = random.randint(1, 3)
        r = req_mod.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": pexels_key},
            params={"query": query, "per_page": 15, "orientation": "landscape", "page": page},
            timeout=20,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])

        if not photos:
            # Retry page 1 as fallback
            r2 = req_mod.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": pexels_key},
                params={"query": query, "per_page": 15, "orientation": "landscape", "page": 1},
                timeout=20,
            )
            r2.raise_for_status()
            photos = r2.json().get("photos", [])

        if not photos:
            raise RuntimeError(f"No Pexels photos for '{query}'")

        # Prefer wide photos, exclude the last-used URL, shuffle for variety
        wide = [p for p in photos if p["width"] / p["height"] >= 1.7]
        pool = wide or photos
        if exclude_url:
            pool = [p for p in pool if p["src"]["large2x"] != exclude_url] or pool
        random.shuffle(pool)
        chosen = pool[0]

        url = chosen["src"]["large2x"]
        img_r = req_mod.get(url, timeout=30, headers=PEXELS_HEADERS)
        img_r.raise_for_status()
        img = Image.open(__import__("io").BytesIO(img_r.content)).convert("RGB")
        print(f"  Pexels [{label}]: {img.width}x{img.height} — {chosen['photographer']} (p{page})")
        return img

    return await asyncio.to_thread(_call)


async def composite_section(
    section: dict,
    session_dir: Path,
    overlay_path: Optional[str] = None,
    font_path: Optional[str] = None,
    force_position: Optional[str] = None,
    background_path: Optional[str] = None,
    out_filename: str = "composited.png",
) -> str:
    """Composite one section image. Returns absolute path to output PNG.

    Uses compose_article_image from src.compositors.compose_article_images.
    background_path: override default background.png location.
    out_filename: override default output filename.
    """
    sec_num = section.get("section_number", 0)
    sec_dir = session_dir / "sections" / str(sec_num)
    bg_path = Path(background_path) if background_path else sec_dir / "background.png"

    if not bg_path.exists():
        raise FileNotFoundError(f"Background not found for section {sec_num}: {bg_path}")

    out_path = str(sec_dir / out_filename)

    _overlay = overlay_path or ARTICLE_OVERLAY
    _font    = font_path    or FONT_ARCHIVO

    background = Image.open(str(bg_path)).convert("RGB")

    def _do_composite():
        from src.compositors.compose_article_images import (
            compose_article_image,
            compose_bottom_line_image,
            compose_faq_image,
        )
        from src.compositors.shared import (
            resize_and_center_crop,
            apply_overlay,
            save_rgb,
        )

        if section.get("is_faq"):
            # FAQ: just resize pool image (no overlay, no text)
            canvas = resize_and_center_crop(background, 1920, 1080)
            save_rgb(canvas, out_path)

        elif section.get("is_bottom_line"):
            # Bottom-line: background + logo overlay, NO text
            canvas = resize_and_center_crop(background, 1920, 1080)
            canvas = apply_overlay(canvas, BOTTOM_LINE_OVERLAY)
            save_rgb(canvas, out_path)

        else:
            # Regular section: background + grey overlay + title text
            compose_article_image(
                h2_text=section.get("text", ""),
                background=background,
                overlay_path=_overlay,
                font_path=_font,
                out_path=out_path,
                force_position=force_position or section.get("force_position"),
            )

    await asyncio.to_thread(_do_composite)
    return out_path


# ---------------------------------------------------------------------------
# ZIP packaging
# ---------------------------------------------------------------------------

def create_zip_package(session_dir: Path, selections: list) -> bytes:
    """Package selected section images into a ZIP with PNG and JPEG versions.

    selections: list of section dicts (each has 'section_number' and 'filename').
    Returns ZIP bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for section in selections:
            sec_num    = section.get("section_number", 0)
            filename   = section.get("filename", f"section_{sec_num}.png")
            comp_path  = session_dir / "sections" / str(sec_num) / "composited.png"

            if not comp_path.exists():
                # Fall back to background
                comp_path = session_dir / "sections" / str(sec_num) / "background.png"

            if not comp_path.exists():
                continue

            img = Image.open(str(comp_path)).convert("RGB")

            # PNG
            png_name = filename
            png_buf = io.BytesIO()
            img.save(png_buf, "PNG", optimize=True)
            zf.writestr(f"PNG/{png_name}", png_buf.getvalue())

            # JPEG
            jpg_name = filename.replace(".png", ".jpg")
            jpg_buf = io.BytesIO()
            img.save(jpg_buf, "JPEG", quality=95, optimize=True)
            zf.writestr(f"JPEG/{jpg_name}", jpg_buf.getvalue())

    return buf.getvalue()
