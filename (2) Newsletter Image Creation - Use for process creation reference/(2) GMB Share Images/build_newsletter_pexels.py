"""
Ask Ross Newsletter — Pexels Stock Image Builder
Produces a 1200 × 900 px PNG for Google My Business + Facebook.
Uses Pexels API for real stock photography (news, real people, real places).

Usage:
    python build_newsletter_pexels.py --list-photos --pexels-query "Donald Trump tariffs"
    python build_newsletter_pexels.py --pexels-query "Donald Trump tariffs" \
        --title1 "How the Trade War Is Hitting Canada's Housing" \
        --intro "The US trade war is rattling Canada's economy..."

Requires:
    .env in project root with PEXELS_API_KEY=...
    assets/ask-ross-overlay.png  (1200×900 RGBA transparent overlay)
    fonts/Aleo-Regular.ttf
    fonts/Aleo-Bold.ttf
    fonts/OpenSans-Regular.ttf
"""

import argparse
import os
from io import BytesIO
from pathlib import Path
from textwrap import dedent

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR   = SCRIPT_DIR.parent


# ---------------------------------------------------------------------------
# Step 1 — blank canvas
# ---------------------------------------------------------------------------

def create_canvas() -> Image.Image:
    return Image.new("RGBA", (1200, 900), (255, 255, 255, 255))


# ---------------------------------------------------------------------------
# Step 2 — fetch banner from Pexels
# ---------------------------------------------------------------------------

def _crop_to_banner(img: Image.Image) -> Image.Image:
    target_w, target_h = 1200, 638
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / src_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def list_pexels_photos(query: str, api_key: str, count: int = 15) -> None:
    response = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": count, "orientation": "landscape"},
        timeout=30,
    )
    response.raise_for_status()
    photos = response.json().get("photos", [])
    if not photos:
        print(f"No results for '{query}'")
        return
    print(f"\nTop {len(photos)} Pexels results for '{query}':")
    for i, p in enumerate(photos):
        name = p['photographer'].encode('ascii', errors='replace').decode('ascii')
        print(f"  [{i}] {name} - {p['width']}x{p['height']}")
        print(f"       {p['url']}")
    print()


def fetch_pexels_photo(
    query: str,
    api_key: str,
    photo_index: int = 0,
    count: int = 15,
) -> tuple[Image.Image, dict]:
    response = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": count, "orientation": "landscape"},
        timeout=30,
    )
    response.raise_for_status()
    photos = response.json().get("photos", [])
    if not photos:
        raise RuntimeError(f"No Pexels results for query: {query!r}")
    if photo_index >= len(photos):
        raise RuntimeError(
            f"--photo-index {photo_index} out of range (found {len(photos)} results). "
            f"Run with --list-photos to see available options."
        )

    photo = photos[photo_index]
    meta = {
        "id": photo["id"],
        "photographer": photo["photographer"],
        "photographer_url": photo["photographer_url"],
        "pexels_url": photo["url"],
    }

    img_url = photo["src"]["large2x"]
    print(f"  Photo [{photo_index}] by {meta['photographer']}")
    print(f"  Page: {meta['pexels_url']}")
    print(f"  Downloading: {img_url}")
    img_response = requests.get(img_url, timeout=60)
    img_response.raise_for_status()

    img = Image.open(BytesIO(img_response.content)).convert("RGB")
    return _crop_to_banner(img), meta


# ---------------------------------------------------------------------------
# Step 3 — composite overlay
# ---------------------------------------------------------------------------

def apply_overlay(canvas: Image.Image) -> Image.Image:
    overlay_path = SCRIPT_DIR / "overlays" / "ask-ross-overlay.png"
    overlay = Image.open(overlay_path).convert("RGBA")
    if overlay.size != (1200, 900):
        overlay = overlay.resize((1200, 900), Image.LANCZOS)
    return Image.alpha_composite(canvas, overlay)


# ---------------------------------------------------------------------------
# Step 4 — draw text
# ---------------------------------------------------------------------------

def _load_font(name: str, size_px: int) -> ImageFont.FreeTypeFont:
    path = SCRIPT_DIR / "fonts" / name
    return ImageFont.truetype(str(path), size_px)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        bbox = font.getbbox(trial)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _balance_lines(lines: list[str], font: ImageFont.FreeTypeFont) -> list[str]:
    """Shape 3-line intro so line 2 is the longest and line 3 has at least 3 words.

    Step 1 — move words from line 1 to line 2 until line 2 is the widest.
    Step 2 — move words from line 2 to line 3 until line 3 has at least 3 words.
    """
    if len(lines) != 3:
        return lines

    def px(text: str) -> int:
        bb = font.getbbox(text)
        return bb[2] - bb[0]

    # Step 1: make line 2 wider than line 1
    while len(lines[0].split()) > 1 and px(lines[0]) >= px(lines[1]):
        words1 = lines[0].split()
        lines[0] = " ".join(words1[:-1])
        lines[1] = words1[-1] + " " + lines[1]

    # Step 2: line 3 minimum 3 words (not a cap — line 3 may have more)
    words3 = lines[2].split()
    while len(words3) < 3:
        words2 = lines[1].split()
        if len(words2) <= 1:
            break
        lines[1] = " ".join(words2[:-1])
        words3 = [words2[-1]] + words3
    lines[2] = " ".join(words3)

    return lines


def _sanitize_text(text: str) -> str:
    return text.replace("—", " - ").replace("–", " - ")


def draw_text(
    canvas: Image.Image,
    title1: str,
    title2: str,
    intro: str,
) -> Image.Image:
    draw = ImageDraw.Draw(canvas)

    f_title1 = _load_font("Aleo-Regular.ttf", 35)
    f_title2 = _load_font("Aleo-Regular.ttf", 35)
    f_intro  = _load_font("OpenSans-Regular.ttf", 27)

    DARK = (26, 26, 26)
    GRAY = (74, 74, 74)

    title1_clean = _sanitize_text(title1)
    if len(title1_clean) > 55:
        print(f"  WARNING: title1 is {len(title1_clean)} chars (max 55). May overflow.")
    draw.text((230, 661.72), title1_clean, font=f_title1, fill=DARK)
    draw.text((230, 704.79), _sanitize_text(title2), font=f_title2, fill=DARK)

    intro_clean = _sanitize_text(intro)
    if len(intro_clean) > 245:
        print(f"  WARNING: intro is {len(intro_clean)} chars (max 245). Capped at 3 lines.")
    intro_lines = _balance_lines(_wrap_text(intro_clean, f_intro, max_width=1010)[:3], f_intro)
    line_height = 40
    for i, line in enumerate(intro_lines):
        draw.text((112, 761.44 + i * line_height), line, font=f_intro, fill=GRAY)

    return canvas


# ---------------------------------------------------------------------------
# Save + QC
# ---------------------------------------------------------------------------

def save_final(canvas: Image.Image, output_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final = Image.new("RGB", canvas.size, (255, 255, 255))
    final.paste(canvas, mask=canvas.split()[3])
    assert final.size == (1200, 900), f"Size mismatch: {final.size}"
    final.save(output_path, "PNG", optimize=True)


def qc(path: str) -> None:
    img = Image.open(path).convert("RGB")
    assert img.size == (1200, 900), f"Bad size: {img.size}"
    px = img.load()
    assert px[600, 800] == (255, 255, 255), f"White band missing: {px[600, 800]}"
    assert px[600, 300] != (0, 0, 0), "Banner not visible"
    title_px = px[300, 680]
    assert title_px != (255, 255, 255), f"TITLE1 not rendered: pixel is white at (300,680)"
    print("  QC passed — white band OK, banner visible, title rendered")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _title_to_filename(title1: str) -> str:
    name = title1.replace(": ", " - ").replace(":", " -")
    invalid = r'\/*?"<>|'
    for ch in invalid:
        name = name.replace(ch, "")
    return name.strip()


def _zoom_banner(banner: Image.Image, zoom: float) -> Image.Image:
    tw, th = 1200, 638
    cw = int(tw / zoom)
    ch = int(th / zoom)
    left = (tw - cw) // 2
    top  = th - ch
    cropped = banner.crop((left, top, left + cw, top + ch))
    return cropped.resize((tw, th), Image.LANCZOS)


# ---------------------------------------------------------------------------
# End-to-end runner
# ---------------------------------------------------------------------------

def build_newsletter(
    pexels_query: str,
    title1: str,
    title2: str,
    intro: str,
    output_path: str | None = None,
    reuse_banner: bool = False,
    banner_zoom: float = 1.0,
    photo_index: int = 0,
    photo_count: int = 15,
) -> None:
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key and not reuse_banner:
        raise RuntimeError("PEXELS_API_KEY not set. Add it to .env in the project root.")

    stem = _title_to_filename(title1)
    out_dir = ROOT_DIR / "out"
    if output_path is None:
        output_path = str(out_dir / f"{stem} GMB Share.png")
    banner_path = str(out_dir / f"{stem} Banner.png")
    credits_path = str(out_dir / f"{stem} Credits.txt")
    os.makedirs(str(out_dir), exist_ok=True)

    print("Step 1: Creating canvas...")
    canvas = create_canvas()

    if reuse_banner and Path(banner_path).exists():
        print("Step 2: Loading existing banner (skipping API)...")
        banner = Image.open(banner_path).convert("RGB")
    else:
        print(f"Step 2: Fetching photo from Pexels (query: '{pexels_query}')...")
        banner, meta = fetch_pexels_photo(pexels_query, api_key, photo_index, photo_count)
        banner.save(banner_path, "PNG", optimize=True)
        print(f"  Banner saved: {banner_path}")
        with open(credits_path, "w", encoding="utf-8") as f:
            f.write(f"Photo by {meta['photographer']}\n")
            f.write(f"Photographer: {meta['photographer_url']}\n")
            f.write(f"Photo page: {meta['pexels_url']}\n")
            f.write("Via Pexels: https://www.pexels.com\n")
        print(f"  Credits saved: {credits_path}")

    if banner_zoom != 1.0:
        print(f"  Applying {banner_zoom}x zoom (bottom-anchored)...")
        banner = _zoom_banner(banner, banner_zoom)

    canvas.paste(banner, (0, 0))
    print(f"  Banner size: {banner.size}")

    print("Step 3: Applying overlay...")
    canvas = apply_overlay(canvas)

    print("Step 4: Drawing text...")
    canvas = draw_text(canvas, title1, title2, intro)

    print(f"Saving to {output_path}...")
    save_final(canvas, output_path)
    print("Running QC...")
    qc(output_path)
    print(f"\nDone: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv(ROOT_DIR / ".env")

    parser = argparse.ArgumentParser(
        description="Build an Ask Ross Newsletter social share image using a Pexels stock photo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Examples:
              # Browse available photos before building
              python build_newsletter_pexels.py --list-photos --pexels-query "Donald Trump tariffs"

              # Build with first result
              python build_newsletter_pexels.py \\
                --pexels-query "Donald Trump tariffs" \\
                --title1 "How the US Trade War Is Hitting Canada's Housing" \\
                --intro "The US trade war is rattling Canada's economy..."

              # Try a different photo from results
              python build_newsletter_pexels.py \\
                --pexels-query "Donald Trump tariffs" --photo-index 2 \\
                --title1 "..." --intro "..." --reuse-banner
        """),
    )
    parser.add_argument("--pexels-query", default="Donald Trump tariffs",
                        help="Search query sent to Pexels")
    parser.add_argument("--title1",
                        default="How the US Trade War Is Hitting Canada's Housing")
    parser.add_argument("--title2", default="| Ask Ross Newsletter")
    parser.add_argument("--intro", default=(
        "The US trade war is rattling Canada's economy - lowering rates, cooling the housing "
        "market, and squeezing landlords. Here's what it means for homeowners, buyers, and renters."
    ))
    parser.add_argument("--output", default=None,
                        help="Override output path (default: derived from title1)")
    parser.add_argument("--reuse-banner", action="store_true",
                        help="Skip API call and reuse existing banner file")
    parser.add_argument("--banner-zoom", type=float, default=1.0,
                        help="Zoom factor for banner crop (1.0=none, 1.25=25%% closer)")
    parser.add_argument("--photo-index", type=int, default=0,
                        help="Which photo to use from results (0 = first/top match)")
    parser.add_argument("--photo-count", type=int, default=15,
                        help="Number of results to fetch from Pexels (max 80)")
    parser.add_argument("--list-photos", action="store_true",
                        help="List available photos for the query and exit without building")

    args = parser.parse_args()

    if args.list_photos:
        api_key = os.environ.get("PEXELS_API_KEY")
        if not api_key:
            raise RuntimeError("PEXELS_API_KEY not set. Add it to .env.")
        list_pexels_photos(args.pexels_query, api_key, args.photo_count)
        return

    build_newsletter(
        pexels_query=args.pexels_query,
        title1=args.title1,
        title2=args.title2,
        intro=args.intro,
        output_path=args.output,
        reuse_banner=args.reuse_banner,
        banner_zoom=args.banner_zoom,
        photo_index=args.photo_index,
        photo_count=args.photo_count,
    )


if __name__ == "__main__":
    main()
