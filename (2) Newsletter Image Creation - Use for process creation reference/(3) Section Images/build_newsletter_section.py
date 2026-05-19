"""
Ask Ross Newsletter — Section Image Builder
Produces a 1200 × 400 px PNG for each newsletter section.

Two section types:
  - cmt      CMT article (canadianmortgagetrends.com) — CMT logo overlay
  - askross  Ask Ross article, client story, newsletter insert — AskRoss grey scrim overlay

Options per type (LOCKED RULES):
  CMT article:   build BOTH options every time
                 --source cmt   (fetches OG image from article URL)
                 --source pexels (Pexels stock alternative)
  Ask Ross:      build AI ONLY by default
                 --source ai    (AI-generated image)
                 --source pexels ONLY if operator explicitly requests it

Faces rule (ABSOLUTE):
  If people appear in the image, their faces must never be cut off.
  Portrait images use top-anchored crop; landscape images use center crop.
  If faces are still cut off after crop, pick a different image.

Usage:
    # CMT article — Option A: fetch from article
    python build_newsletter_section.py \
        --source cmt --cmt-url "https://www.canadianmortgagetrends.com/..." \
        --name "Retirement Mortgage CMT"

    # CMT article — Option B: Pexels (always build this for CMT)
    python build_newsletter_section.py \
        --source pexels --pexels-query "retirement couple Canadian home" \
        --section-type cmt --name "Retirement Mortgage Pexels"

    # Ask Ross — AI (default, build this only)
    python build_newsletter_section.py \
        --source ai --banner-prompt "Wide 16:4 panoramic, Bank of Canada Ottawa..." \
        --section-type askross --name "BoC Rate AI"

    # Reuse raw image, reapply overlay
    python build_newsletter_section.py \
        --source custom --banner-image "out/BoC Rate AI Section Raw.png" \
        --section-type askross --name "BoC Rate AI v2"

Requires:
    (3) Section Images/CMT logo.png
    (3) Section Images/AskRoss Logo + Grey Transparent Layer.png
    .env: OPENROUTER_IMAGE_API_KEY, PEXELS_API_KEY
"""

import argparse
import base64
import os
import re
from io import BytesIO
from pathlib import Path
from textwrap import dedent

import requests
from dotenv import load_dotenv
from PIL import Image

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR   = SCRIPT_DIR.parent
SECTION_W, SECTION_H = 1200, 400

OVERLAY_ASKROSS = SCRIPT_DIR / "overlays" / "AskRoss Logo + Grey Transparent Layer.png"
OVERLAY_CMT     = SCRIPT_DIR / "overlays" / "CMT logo.png"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------

def create_canvas() -> Image.Image:
    return Image.new("RGBA", (SECTION_W, SECTION_H), (255, 255, 255, 255))


# ---------------------------------------------------------------------------
# Image sources
# ---------------------------------------------------------------------------

def _resize_to_section(img: Image.Image) -> Image.Image:
    """Crop to 1200×400. Portrait sources use top-anchored crop to preserve faces."""
    src_ratio    = img.width / img.height
    target_ratio = SECTION_W / SECTION_H
    if src_ratio > target_ratio:
        new_h = SECTION_H
        new_w = int(new_h * src_ratio)
    else:
        new_w = SECTION_W
        new_h = int(new_w / src_ratio)
    img  = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - SECTION_W) // 2
    # Portrait sources: faces are near the top — top-anchored crop preserves them.
    # Landscape sources: center crop is correct (subjects typically centered vertically).
    top = 0 if src_ratio < 1.0 else (new_h - SECTION_H) // 2
    return img.crop((left, top, left + SECTION_W, top + SECTION_H))


def _get_image_cmt(url: str) -> Image.Image:
    """Fetch the OG/feature image from a CMT article URL."""
    print(f"  Fetching CMT article: {url}")
    r = requests.get(url, timeout=15, headers=HEADERS)
    r.raise_for_status()
    html = r.text
    img_url = None
    for pattern in [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            img_url = m.group(1).strip()
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            break
    if not img_url:
        raise RuntimeError(f"No OG image found at {url}")
    print(f"  OG image: {img_url}")
    ir = requests.get(img_url, timeout=30, headers=HEADERS)
    ir.raise_for_status()
    return Image.open(BytesIO(ir.content)).convert("RGB")


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
    data    = r.json()
    img_url = data["choices"][0]["message"]["images"][0]["image_url"]["url"]
    b64     = img_url.split(",", 1)[1]
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")


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
    ph   = photos[index]
    ir   = requests.get(ph["src"]["large2x"], timeout=30, headers=HEADERS)
    ir.raise_for_status()
    meta = {
        "image_url":  ph["src"]["large2x"],
        "source_url": ph["url"],
        "title":      f"Photo by {ph['photographer']} on Pexels",
    }
    print(f"  [{index}] {ph['width']}x{ph['height']} — {ph['photographer']}")
    return Image.open(BytesIO(ir.content)).convert("RGB"), meta


def _get_image_custom(path: str) -> Image.Image:
    p = Path(path)
    if not p.is_absolute():
        p = SCRIPT_DIR / p
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")
    return Image.open(p).convert("RGB")


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------

def _apply_overlay(canvas: Image.Image, section_type: str) -> Image.Image:
    overlay_path = OVERLAY_CMT if section_type == "cmt" else OVERLAY_ASKROSS
    overlay = Image.open(overlay_path).convert("RGBA")
    if overlay.size != (SECTION_W, SECTION_H):
        overlay = overlay.resize((SECTION_W, SECTION_H), Image.LANCZOS)
    return Image.alpha_composite(canvas.convert("RGBA"), overlay)


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
    assert img.size == (SECTION_W, SECTION_H), f"Wrong size: {img.size}"
    px = img.load()
    assert px[600, 200] != (0, 0, 0), "Section image appears blank"
    print(f"  QC passed — {SECTION_W}×{SECTION_H}, not blank")


def _name_to_filename(name: str) -> str:
    name = name.replace(": ", " - ").replace(":", " -")
    for ch in r'\/*?"<>|':
        name = name.replace(ch, "")
    return name.strip()


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build_section(
    source: str,
    name: str,
    section_type: str,
    cmt_url: str = None,
    banner_prompt: str = None,
    pexels_query: str = None,
    pexels_index: int = 0,
    pexels_count: int = 15,
    pexels_list: bool = False,
    banner_image: str = None,
    output_dir: str = None,
) -> None:
    out_dir  = Path(output_dir) if output_dir else ROOT_DIR / "out"
    os.makedirs(str(out_dir), exist_ok=True)
    stem        = _name_to_filename(name)
    raw_path    = str(out_dir / f"{stem} Section Raw.png")
    final_path  = str(out_dir / f"{stem} Section.png")
    credits_path = str(out_dir / f"{stem} Section Credits.txt")

    # ── Step 1: get image
    print(f"Step 1: Getting image (source={source})...")
    load_dotenv(ROOT_DIR / ".env")
    meta = {}

    if source == "cmt":
        if not cmt_url:
            raise RuntimeError("--cmt-url is required for --source cmt")
        raw = _get_image_cmt(cmt_url)

    elif source == "ai":
        api_key = os.environ.get("OPENROUTER_IMAGE_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_IMAGE_API_KEY not set in .env")
        if not banner_prompt:
            raise RuntimeError("--banner-prompt is required for --source ai")
        raw = _get_image_ai(banner_prompt, api_key)

    elif source == "pexels":
        api_key = os.environ.get("PEXELS_API_KEY")
        if not api_key:
            raise RuntimeError("PEXELS_API_KEY not set in .env")
        if not pexels_query:
            raise RuntimeError("--pexels-query is required for --source pexels")
        result = _get_image_pexels(pexels_query, api_key, pexels_index, pexels_count, pexels_list)
        if pexels_list:
            return
        raw, meta = result

    elif source == "custom":
        if not banner_image:
            raise RuntimeError("--banner-image is required for --source custom")
        raw = _get_image_custom(banner_image)

    else:
        raise ValueError(f"Unknown source: {source!r}")

    # ── Step 2: crop to 1200×400
    print("Step 2: Resizing to 1200×400...")
    raw = _resize_to_section(raw)
    print(f"  Saving raw: {raw_path}")
    _save_rgb(raw, raw_path)

    if meta:
        with open(credits_path, "w", encoding="utf-8") as f:
            f.write(f"Title:  {meta.get('title', '')}\n")
            f.write(f"Source: {meta.get('source_url', '')}\n")
            f.write(f"Image:  {meta.get('image_url', '')}\n")

    # ── Step 3: apply overlay
    print(f"Step 3: Applying overlay (type={section_type})...")
    canvas = create_canvas()
    canvas.paste(raw, (0, 0))
    canvas = _apply_overlay(canvas, section_type)

    # ── Step 4: save
    print(f"Step 4: Saving: {final_path}")
    _save_rgb(canvas, final_path)
    qc(final_path)
    print(f"\nDone: {final_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv(ROOT_DIR / ".env")

    parser = argparse.ArgumentParser(
        description="Build a 1200×400 Ask Ross Newsletter section image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Rules:
              CMT sections    → always build BOTH: article OG image + Pexels
              Ask Ross sections → build AI only; Pexels only if requested
              Faces rule      → if people in image, faces must never be cut off

            Examples:
              # CMT — Option A (fetch article OG image)
              python build_newsletter_section.py \\
                --source cmt --cmt-url "https://www.canadianmortgagetrends.com/..." \\
                --name "Retirement Mortgage CMT"

              # CMT — Option B (Pexels — always build this for CMT)
              python build_newsletter_section.py \\
                --source pexels --pexels-query "retirement couple Canadian home" \\
                --section-type cmt --name "Retirement Mortgage Pexels"

              # Ask Ross — AI (default, build this only)
              python build_newsletter_section.py \\
                --source ai --banner-prompt "Wide 16:4 panoramic, Bank of Canada Ottawa..." \\
                --section-type askross --name "BoC Rate AI"

              # Reuse raw, reapply overlay
              python build_newsletter_section.py \\
                --source custom --banner-image "out/BoC Rate AI Section Raw.png" \\
                --section-type askross --name "BoC Rate AI v2"
        """),
    )

    parser.add_argument("--source", required=True,
                        choices=["cmt", "ai", "pexels", "custom"])
    parser.add_argument("--name", default=None,
                        help="Output filename stem — required for builds")
    parser.add_argument("--section-type", choices=["askross", "cmt"], default=None,
                        help="Overlay type. Auto-set to 'cmt' for --source cmt. Required otherwise.")
    parser.add_argument("--cmt-url",       help="[cmt] Full CMT article URL")
    parser.add_argument("--banner-prompt", help="[ai] Image generation prompt")
    parser.add_argument("--pexels-query",  help="[pexels] Search query")
    parser.add_argument("--photo-index",   type=int, default=0)
    parser.add_argument("--photo-count",   type=int, default=15)
    parser.add_argument("--list-photos",   action="store_true")
    parser.add_argument("--banner-image",  help="[custom] Path to image")
    parser.add_argument("--output-dir",    default=None)

    args = parser.parse_args()

    # Defaults
    if args.source == "cmt" and not args.section_type:
        args.section_type = "cmt"

    list_mode = args.list_photos
    if not list_mode:
        if not args.name:
            parser.error("--name is required when building an image")
        if not args.section_type:
            parser.error("--section-type (askross or cmt) is required for --source ai/pexels/custom")

    args.name = args.name or "preview"

    build_section(
        source       = args.source,
        name         = args.name,
        section_type = args.section_type or "askross",
        cmt_url      = args.cmt_url,
        banner_prompt= args.banner_prompt,
        pexels_query = args.pexels_query,
        pexels_index = args.photo_index,
        pexels_count = args.photo_count,
        pexels_list  = args.list_photos,
        banner_image = args.banner_image,
        output_dir   = args.output_dir,
    )


if __name__ == "__main__":
    main()
