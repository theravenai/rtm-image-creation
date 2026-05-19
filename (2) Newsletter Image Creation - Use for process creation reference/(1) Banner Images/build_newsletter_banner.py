"""
Ask Ross Newsletter — Banner Image Builder
Produces a 1200 × 800 px PNG for newsletter feature images.

Workflow:
    1. Get image (AI / Sonar / Pexels / Custom)
    2. Save {name} Banner Raw.png   (1200×800, no overlay, no text)
    3. Apply gradient + logo overlay
    4. Add text if appropriate (see --title, --text-position, --no-text)
    5. Save {name} Banner.png

After banner approval, run build_newsletter_custom.py with:
    --banner-image "out/{name} Banner Raw.png"
to produce the GMB Share image.

Usage:
    # AI-generated image
    python build_newsletter_banner.py --source ai \\
        --banner-prompt "..." --name "Fall Market Crossroads"

    # Sonar (browse first, then build)
    python build_newsletter_banner.py --source sonar \\
        --sonar-query "Mark Carney 2025" --list-images
    python build_newsletter_banner.py --source sonar \\
        --sonar-query "Mark Carney 2025" --use-cache --image-index 1 \\
        --name "Carney Wins" --no-text

    # Pexels
    python build_newsletter_banner.py --source pexels \\
        --pexels-query "Canadian housing autumn" --name "Fall Market" \\
        --title "Buy Now or Wait It Out?" --text-position lower-left

    # Custom image
    python build_newsletter_banner.py --source custom \\
        --banner-image "in/photo.jpg" --name "My Issue" --no-text

Requires:
    (1) Banner Images/Ask Ross Logo + Gradient Layer - Feature Image.png
    fonts/Archivo_Black/ArchivoBlack-Regular.ttf
    .env: OPENROUTER_IMAGE_API_KEY, PERPLEXITY_API_KEY, PEXELS_API_KEY
"""

import argparse
import base64
import json
import os
import re
from io import BytesIO
from pathlib import Path
from textwrap import dedent

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR   = SCRIPT_DIR.parent
BANNER_W, BANNER_H = 1200, 800

# Text layout constants
FONT_SIZE           = 45     # Archivo Black size
TEXT_LEFT_MARGIN    = 193    # just right of ASKROSS.CA logo box (logo spans x=17–190)
TEXT_MAX_WIDTH_LEFT = 800    # left-aligned positions (allows 2-line wrap at 45px)
TEXT_MAX_WIDTH_CENTER = 900  # center position
TEXT_LINE_HEIGHT    = 55     # FONT_SIZE + 10px leading
UPPER_LEFT_Y        = 213    # upper third
LOWER_LEFT_BOTTOM_PAD = 140  # text_y≈550 for 2 lines (solidly in lower third)

# Drop shadow: direction -45° (lower-right), offset 60px, blur 50, opacity 30%
SHADOW_OFFSET  = 1    # Distance: 1px (Photoshop), angle 40°
SHADOW_BLUR    = 3    # Size: 6px → PIL GaussianBlur radius ≈ 3
SHADOW_OPACITY = 114  # Opacity: 45% (0.45 × 255)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Keywords that trigger auto no-text (subject speaks for itself)
NO_TEXT_SUBJECTS = {
    "ross", "ross taylor", "trump", "donald trump", "carney", "mark carney",
    "politician", "president", "prime minister", "trudeau", "poilievre",
}


# ---------------------------------------------------------------------------
# Image source: AI (OpenRouter / Gemini Flash Image)
# ---------------------------------------------------------------------------

def _get_image_ai(prompt: str, api_key: str) -> Image.Image:
    print("  Generating image via OpenRouter (Gemini Flash Image)...")
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "google/gemini-2.5-flash-image",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    img_url = data["choices"][0]["message"]["images"][0]["image_url"]["url"]
    b64 = img_url.split(",", 1)[1]
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")


# ---------------------------------------------------------------------------
# Image source: Sonar (Perplexity)
# ---------------------------------------------------------------------------

SONAR_DOMAINS = [
    "cnn.com", "nytimes.com", "thetimes.co.uk", "globalnews.ca",
    "reuters.com", "apnews.com", "bbc.com", "cbc.ca", "theglobeandmail.com", "ctv.ca",
]
SONAR_CACHE = ROOT_DIR / "out" / "_banner_sonar_cache.json"


def _sonar_api(query: str, api_key: str, recency: str) -> tuple[str, list, list]:
    payload = {
        "model": "sonar",
        "return_images": True,
        "search_recency_filter": recency,
        "search_domain_filter": SONAR_DOMAINS,
        "return_citations": True,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Find recent editorial news photographs. Landscape (16:9) only. "
                    "No illustrations, graphics, watermarks, or baked-in text overlays."
                ),
            },
            {"role": "user", "content": f"Find recent news photographs of {query}. Photographs only."},
        ],
    }
    r = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload, timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])
    raw_images = data.get("images", [])
    images = []
    for item in raw_images:
        if isinstance(item, str):
            images.append({"image_url": item, "source_url": "", "title": "(Sonar image)"})
        elif isinstance(item, dict):
            url = item.get("url") or item.get("image_url") or ""
            if url:
                images.append({
                    "image_url": url,
                    "source_url": item.get("origin_url", ""),
                    "title": str(item.get("title", ""))[:90],
                })
    return content, citations, images


def _get_og_image(page_url: str):
    try:
        r = requests.get(page_url, timeout=10, headers=HEADERS)
        if r.status_code != 200:
            return None
        html = r.text
        title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        title = title_m.group(1).strip() if title_m else page_url
        for pattern in [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        ]:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                img_url = m.group(1).strip()
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                return img_url, title
    except Exception:
        pass
    return None


def _download_image(url: str) -> Image.Image:
    r = requests.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")


def _collect_sonar_candidates(query: str, api_key: str, count: int, recency: str) -> list:
    print(f"  Sonar search: '{query}' (recency={recency})...")
    content, citations, direct = _sonar_api(query, api_key, recency)
    candidates = []
    for img in direct[:count]:
        if img["image_url"]:
            candidates.append(img)
    remaining = max(0, count - len(candidates))
    for url in citations[:remaining]:
        result = _get_og_image(url)
        if result:
            img_url, title = result
            candidates.append({"image_url": img_url, "source_url": url, "title": title[:90]})
    return candidates


def _get_image_sonar(
    query: str, api_key: str,
    image_index: int | None = None, count: int = 10,
    recency: str = "month", use_cache: bool = False, list_only: bool = False,
) -> tuple[Image.Image | None, dict]:
    if use_cache and SONAR_CACHE.exists():
        with open(SONAR_CACHE, encoding="utf-8") as f:
            candidates = json.load(f)
        print(f"  Using cached list ({len(candidates)} items).")
    else:
        candidates = _collect_sonar_candidates(query, api_key, count, recency)
        os.makedirs(str(SCRIPT_DIR / "out"), exist_ok=True)
        with open(SONAR_CACHE, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2)

    if list_only:
        print(f"\n{len(candidates)} candidates for '{query}':")
        for i, c in enumerate(candidates):
            try:
                if "ytimg.com" in c["image_url"] or "youtube.com" in c["image_url"]:
                    print(f"  [{i}] YouTube — skipped | {c['title']}")
                    continue
                img = _download_image(c["image_url"])
                ratio = img.width / img.height
                status = "16:9 widescreen" if ratio >= 1.7 else ("landscape" if ratio >= 1.5 else "PORTRAIT")
                print(f"  [{i}] {img.width}x{img.height} ({ratio:.2f}) {status}")
                print(f"       {c['title']}")
                print(f"       {c['image_url']}")
            except Exception as e:
                print(f"  [{i}] error ({e}) | {c['title']}")
        print("\nRun with --use-cache --image-index N to build with a specific candidate.")
        return None, {}

    if not candidates:
        raise RuntimeError(f"No images found for '{query}'")

    if image_index is not None:
        c = candidates[image_index]
        print(f"  [{image_index}] {c['title']}")
        img = _download_image(c["image_url"])
        print(f"  Size: {img.width}x{img.height}")
        return img, c

    # Auto-select: prefer 16:9, skip YouTube/portrait
    landscape_fallback = None
    for i, c in enumerate(candidates):
        url = c["image_url"]
        if "ytimg.com" in url or "youtube.com" in url:
            continue
        try:
            img = _download_image(url)
            ratio = img.width / img.height
            if ratio >= 1.7:
                print(f"  [{i}] {img.width}x{img.height} 16:9 — auto-selected")
                return img, c
            elif ratio >= 1.5 and landscape_fallback is None:
                landscape_fallback = (img, c)
        except Exception:
            pass
    if landscape_fallback:
        img, c = landscape_fallback
        print(f"  No 16:9 found — using landscape fallback: {c['title']}")
        return img, c
    raise RuntimeError("No landscape images found. Run --list-images and use --image-index.")


# ---------------------------------------------------------------------------
# Image source: Pexels
# ---------------------------------------------------------------------------

def _get_image_pexels(
    query: str, api_key: str,
    index: int = 0, count: int = 15, list_only: bool = False,
) -> tuple[Image.Image | None, dict]:
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": count, "orientation": "landscape"},
        timeout=15,
    )
    r.raise_for_status()
    photos = r.json().get("photos", [])
    if not photos:
        raise RuntimeError(f"No Pexels photos for '{query}'")

    if list_only:
        print(f"\n{len(photos)} Pexels results for '{query}':")
        for i, ph in enumerate(photos):
            photographer = ph["photographer"].encode("ascii", errors="replace").decode("ascii")
            print(f"  [{i}] {ph['width']}x{ph['height']} — {photographer}")
            print(f"       {ph['url']}")
        return None, {}

    if index >= len(photos):
        raise RuntimeError(f"--photo-index {index} out of range ({len(photos)} results).")
    ph = photos[index]
    print(f"  [{index}] Downloading Pexels photo...")
    img_r = requests.get(ph["src"]["large2x"], timeout=30, headers=HEADERS)
    img_r.raise_for_status()
    meta = {
        "image_url": ph["src"]["large2x"],
        "source_url": ph["url"],
        "title": f"Photo by {ph['photographer']} on Pexels",
    }
    return Image.open(BytesIO(img_r.content)).convert("RGB"), meta


# ---------------------------------------------------------------------------
# Image source: Custom
# ---------------------------------------------------------------------------

def _get_image_custom(path: str) -> Image.Image:
    p = Path(path)
    if not p.is_absolute():
        p = SCRIPT_DIR / p
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}\nDrop your image into in/ and pass the path.")
    return Image.open(p).convert("RGB")


# ---------------------------------------------------------------------------
# Banner pipeline
# ---------------------------------------------------------------------------

def _resize_to_banner(img: Image.Image) -> Image.Image:
    """Center-crop and resize to 1200×800."""
    src_ratio = img.width / img.height
    target_ratio = BANNER_W / BANNER_H
    if src_ratio > target_ratio:
        new_h = BANNER_H
        new_w = int(new_h * src_ratio)
    else:
        new_w = BANNER_W
        new_h = int(new_w / src_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - BANNER_W) // 2
    top = (new_h - BANNER_H) // 2
    return img.crop((left, top, left + BANNER_W, top + BANNER_H))


def _zoom_banner(img: Image.Image, zoom: float) -> Image.Image:
    cw, ch = int(BANNER_W / zoom), int(BANNER_H / zoom)
    left = (BANNER_W - cw) // 2
    top = BANNER_H - ch
    return img.crop((left, top, left + cw, top + ch)).resize((BANNER_W, BANNER_H), Image.LANCZOS)


def _apply_overlay(canvas: Image.Image) -> Image.Image:
    overlay_path = SCRIPT_DIR / "overlays" / "Logo + Grey Transparent Layer - Banner.png"
    overlay = Image.open(overlay_path).convert("RGBA")
    if overlay.size != (BANNER_W, BANNER_H):
        overlay = overlay.resize((BANNER_W, BANNER_H), Image.LANCZOS)
    return Image.alpha_composite(canvas.convert("RGBA"), overlay)


# ---------------------------------------------------------------------------
# Text rendering (Archivo Black + drop shadow)
# ---------------------------------------------------------------------------

def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], []
    for word in words:
        trial = " ".join(current + [word])
        bb = font.getbbox(trial)
        if bb[2] - bb[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_banner_text(canvas: Image.Image, title: str, position: str) -> Image.Image:
    """Render title text with drop shadow at the specified position."""
    font_path = SCRIPT_DIR / "fonts" / "Archivo_Black" / "ArchivoBlack-Regular.ttf"
    font = ImageFont.truetype(str(font_path), FONT_SIZE)

    if position == "center":
        lines = _wrap_text(title, font, TEXT_MAX_WIDTH_CENTER)
        total_h = len(lines) * TEXT_LINE_HEIGHT
        text_y = (BANNER_H - total_h) // 2
        align = "center"
    elif position == "upper-left":
        lines = _wrap_text(title, font, TEXT_MAX_WIDTH_LEFT)
        text_y = UPPER_LEFT_Y
        align = "left"
    else:  # lower-left
        lines = _wrap_text(title, font, TEXT_MAX_WIDTH_LEFT)
        total_h = len(lines) * TEXT_LINE_HEIGHT
        text_y = BANNER_H - total_h - LOWER_LEFT_BOTTOM_PAD
        align = "left"

    def line_x(line: str) -> int:
        if align == "center":
            bb = font.getbbox(line)
            return (BANNER_W - (bb[2] - bb[0])) // 2
        return TEXT_LEFT_MARGIN

    # Build shadow layer: draw black text at offset, then blur
    shadow_layer = Image.new("RGBA", (BANNER_W, BANNER_H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    for i, line in enumerate(lines):
        ly = text_y + i * TEXT_LINE_HEIGHT
        shadow_draw.text(
            (line_x(line) + SHADOW_OFFSET, ly + SHADOW_OFFSET),
            line, font=font, fill=(0, 0, 0, SHADOW_OPACITY),
        )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR))

    # Composite: existing canvas → shadow → white text
    result = Image.alpha_composite(canvas.convert("RGBA"), shadow_layer)
    text_draw = ImageDraw.Draw(result)
    for i, line in enumerate(lines):
        ly = text_y + i * TEXT_LINE_HEIGHT
        text_draw.text((line_x(line), ly), line, font=font, fill=(255, 255, 255, 255))

    return result


# ---------------------------------------------------------------------------
# Auto-decision helpers
# ---------------------------------------------------------------------------

def _should_add_text(hint: str) -> bool:
    """Return False if the subject speaks for itself (Ross, politician, named person)."""
    hint_lower = hint.lower()
    for kw in NO_TEXT_SUBJECTS:
        if kw in hint_lower:
            print(f"  Auto no-text: '{hint}' matched keyword '{kw}'")
            return False
    return True


def _auto_text_position(canvas: Image.Image) -> str:
    """Choose the text position with the darkest average area (best for white text)."""
    try:
        import numpy as np
        arr = __import__("numpy").array(canvas.convert("RGB")).astype(float)

        def lum(x1, y1, x2, y2):
            r = arr[y1:y2, x1:x2]
            return (0.299 * r[:, :, 0] + 0.587 * r[:, :, 1] + 0.114 * r[:, :, 2]).mean()

        scores = {
            "upper-left": lum(0, UPPER_LEFT_Y - 20, 600, UPPER_LEFT_Y + TEXT_LINE_HEIGHT * 3),
            "lower-left": lum(0, BANNER_H - 160, 600, BANNER_H - 40),
            "center":     lum(250, BANNER_H // 2 - 60, 950, BANNER_H // 2 + 60),
        }
        best = min(scores, key=scores.get)
        print(f"  Auto text position: '{best}' "
              f"(lum — upper-left:{scores['upper-left']:.0f}, "
              f"lower-left:{scores['lower-left']:.0f}, "
              f"center:{scores['center']:.0f})")
        return best
    except ImportError:
        print("  numpy not available — defaulting to lower-left")
        return "lower-left"


# ---------------------------------------------------------------------------
# Save + QC
# ---------------------------------------------------------------------------

def _save_rgb(img: Image.Image, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    img.save(path, "PNG", optimize=True)


def qc(path: str) -> None:
    img = Image.open(path).convert("RGB")
    assert img.size == (BANNER_W, BANNER_H), f"Wrong size: {img.size}"
    px = img.load()
    assert px[600, 400] != (0, 0, 0), "Banner appears blank"
    print(f"  QC passed — {BANNER_W}×{BANNER_H}, not blank")


def _title_to_filename(name: str) -> str:
    name = name.replace(": ", " - ").replace(":", " -")
    for ch in r'\/*?"<>|':
        name = name.replace(ch, "")
    return name.strip()


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build_banner(
    source: str,
    name: str,
    # AI
    banner_prompt: str = None,
    # Sonar
    sonar_query: str = None,
    sonar_recency: str = "month",
    sonar_index: int | None = None,
    sonar_count: int = 10,
    sonar_use_cache: bool = False,
    sonar_list_images: bool = False,
    # Pexels
    pexels_query: str = None,
    pexels_index: int = 0,
    pexels_count: int = 15,
    pexels_list_photos: bool = False,
    # Custom
    banner_image: str = None,
    # Text
    title: str = None,
    text_position: str = None,
    force_text: bool = False,
    no_text: bool = False,
    subject_hint: str = "",
    # Shared
    banner_zoom: float = 1.0,
    reuse_raw: bool = False,
    output_dir: str = None,
) -> None:

    out_dir = Path(output_dir) if output_dir else ROOT_DIR / "out"
    os.makedirs(str(out_dir), exist_ok=True)
    stem = _title_to_filename(name)
    raw_path     = str(out_dir / f"{stem} Banner Raw.png")
    final_path   = str(out_dir / f"{stem} Banner.png")
    credits_path = str(out_dir / f"{stem} Banner Credits.txt")

    # ── Step 1: get image
    meta = {}
    if reuse_raw and Path(raw_path).exists():
        print("Step 1: Reusing existing Banner Raw (skipping fetch)...")
        raw = Image.open(raw_path).convert("RGB")
    else:
        print(f"Step 1: Getting image (source={source})...")
        load_dotenv(ROOT_DIR / ".env")

        if source == "ai":
            api_key = os.environ.get("OPENROUTER_IMAGE_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                raise RuntimeError("OPENROUTER_IMAGE_API_KEY not set in .env")
            if not banner_prompt:
                raise RuntimeError("--banner-prompt is required for --source ai")
            raw = _get_image_ai(banner_prompt, api_key)

        elif source == "sonar":
            api_key = os.environ.get("PERPLEXITY_API_KEY")
            if not api_key:
                raise RuntimeError("PERPLEXITY_API_KEY not set in .env")
            if not sonar_query:
                raise RuntimeError("--sonar-query is required for --source sonar")
            result = _get_image_sonar(
                sonar_query, api_key, sonar_index, sonar_count,
                sonar_recency, sonar_use_cache, sonar_list_images,
            )
            if sonar_list_images:
                return
            raw, meta = result

        elif source == "pexels":
            api_key = os.environ.get("PEXELS_API_KEY")
            if not api_key:
                raise RuntimeError("PEXELS_API_KEY not set in .env")
            if not pexels_query:
                raise RuntimeError("--pexels-query is required for --source pexels")
            result = _get_image_pexels(pexels_query, api_key, pexels_index, pexels_count, pexels_list_photos)
            if pexels_list_photos:
                return
            raw, meta = result

        elif source == "custom":
            if not banner_image:
                raise RuntimeError("--banner-image is required for --source custom")
            raw = _get_image_custom(banner_image)

        else:
            raise ValueError(f"Unknown source: {source!r}")

        # ── Step 2: resize to 1200×800 and save raw
        print("Step 2: Resizing to 1200×800...")
        raw = _resize_to_banner(raw)
        if banner_zoom != 1.0:
            print(f"  Applying {banner_zoom}x zoom (bottom-anchored)...")
            raw = _zoom_banner(raw, banner_zoom)

        print(f"  Saving raw: {raw_path}")
        _save_rgb(raw, raw_path)

        if meta:
            with open(credits_path, "w", encoding="utf-8") as f:
                f.write(f"Title:  {meta.get('title', '')}\n")
                f.write(f"Source: {meta.get('source_url', '')}\n")
                f.write(f"Image:  {meta.get('image_url', '')}\n")

    # ── Step 3: apply overlay
    print("Step 3: Applying gradient + logo overlay...")
    canvas = _apply_overlay(raw)

    # ── Step 4: text decision
    if no_text:
        print("Step 4: No text (--no-text).")
        add_text = False
    elif force_text or title:
        print("Step 4: Adding text.")
        add_text = True
    else:
        hint = subject_hint or sonar_query or pexels_query or name
        add_text = _should_add_text(hint)

    if add_text:
        if not title:
            print("  WARNING: no --title provided. Pass --title 'Your engaging hook' for best results.")
            title = name
        pos = text_position or _auto_text_position(canvas)
        print(f"  Position: '{pos}' | Text: {title[:60]}")
        canvas = draw_banner_text(canvas, title, pos)
    else:
        if not no_text:
            print("Step 4: Text skipped — subject identified as self-explanatory.")

    # ── Step 5: save final
    print(f"Step 5: Saving banner: {final_path}")
    _save_rgb(canvas, final_path)
    qc(final_path)

    print(f"\nDone.")
    print(f"  Raw (for GMB Share): {raw_path}")
    print(f"  Final banner:        {final_path}")
    if Path(credits_path).exists():
        print(f"  Credits:             {credits_path}")
    print(f"\nNext: get banner approved, then run:")
    print(f'  python build_newsletter_custom.py --banner-image "{raw_path}" --title1 "..." --intro "..."')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv(ROOT_DIR / ".env")

    parser = argparse.ArgumentParser(
        description="Build an Ask Ross Newsletter banner image (1200×800).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Examples:
              # AI — lifestyle/seasonal/abstract
              python build_newsletter_banner.py --source ai \\
                --banner-prompt "..." --name "Fall Market Crossroads"

              # Sonar — browse candidates first
              python build_newsletter_banner.py --source sonar \\
                --sonar-query "Mark Carney 2025" --list-images

              # Sonar — build with chosen image, no text (politician)
              python build_newsletter_banner.py --source sonar \\
                --sonar-query "Mark Carney 2025" --use-cache --image-index 1 \\
                --name "Carney Housing" --no-text

              # Pexels — with engaging title, lower-left
              python build_newsletter_banner.py --source pexels \\
                --pexels-query "Canadian housing autumn" --name "Fall Market" \\
                --title "Buy Now or Wait It Out?" --text-position lower-left

              # Custom image — no text (Ross's photo)
              python build_newsletter_banner.py --source custom \\
                --banner-image "in/ross-photo.jpg" --name "Ross Event" --no-text

              # Adjust text only (no re-fetch)
              python build_newsletter_banner.py --source custom \\
                --banner-image "in/photo.jpg" --name "Fall Market" \\
                --reuse-raw --title "New title" --text-position upper-left
        """),
    )

    # Required
    parser.add_argument("--source", required=True, choices=["ai", "sonar", "pexels", "custom"],
                        help="Image source")
    parser.add_argument("--name", default=None,
                        help="Image name for output filenames (e.g. 'Fall Market Crossroads'). "
                             "Required for build; not needed for --list-images / --list-photos.")

    # AI
    parser.add_argument("--banner-prompt", help="[ai] Image generation prompt")

    # Sonar
    parser.add_argument("--sonar-query", help="[sonar] Perplexity search query")
    parser.add_argument("--recency", default="month", choices=["day", "week", "month", "year"])
    parser.add_argument("--image-index", type=int, default=None)
    parser.add_argument("--image-count", type=int, default=10)
    parser.add_argument("--list-images", action="store_true")
    parser.add_argument("--use-cache", action="store_true")

    # Pexels
    parser.add_argument("--pexels-query", help="[pexels] Pexels search query")
    parser.add_argument("--photo-index", type=int, default=0)
    parser.add_argument("--photo-count", type=int, default=15)
    parser.add_argument("--list-photos", action="store_true")

    # Custom
    parser.add_argument("--banner-image", help="[custom] Path to image file")

    # Text
    parser.add_argument("--title", default=None,
                        help="Engaging hook headline for the banner (not the newsletter title1)")
    parser.add_argument("--text-position", choices=["upper-left", "lower-left", "center"],
                        default=None, help="Text position. Default: auto (darkest area)")
    parser.add_argument("--text", dest="force_text", action="store_true",
                        help="Force text on even if auto-decision would skip it")
    parser.add_argument("--no-text", action="store_true",
                        help="Force no text regardless of subject")
    parser.add_argument("--subject-hint", default="",
                        help="Hint for auto no-text logic (e.g. 'Ross Taylor', 'Trump')")

    # Shared
    parser.add_argument("--banner-zoom", type=float, default=1.0,
                        help="Zoom into lower portion of image (1.0=none, 1.2=20% closer)")
    parser.add_argument("--reuse-raw", action="store_true",
                        help="Skip image fetch, reuse existing Banner Raw PNG (text/layout tweaks)")
    parser.add_argument("--output-dir", default=None)

    args = parser.parse_args()

    # --name only required when actually building (not for list operations)
    list_mode = args.list_images or args.list_photos
    if not list_mode and not args.name:
        parser.error("--name is required when building an image")

    args.name = args.name or "preview"

    build_banner(
        source=args.source,
        name=args.name,
        banner_prompt=args.banner_prompt,
        sonar_query=args.sonar_query,
        sonar_recency=args.recency,
        sonar_index=args.image_index,
        sonar_count=args.image_count,
        sonar_use_cache=args.use_cache,
        sonar_list_images=args.list_images,
        pexels_query=args.pexels_query,
        pexels_index=args.photo_index,
        pexels_count=args.photo_count,
        pexels_list_photos=args.list_photos,
        banner_image=args.banner_image,
        title=args.title,
        text_position=args.text_position,
        force_text=args.force_text,
        no_text=args.no_text,
        subject_hint=args.subject_hint,
        banner_zoom=args.banner_zoom,
        reuse_raw=args.reuse_raw,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
