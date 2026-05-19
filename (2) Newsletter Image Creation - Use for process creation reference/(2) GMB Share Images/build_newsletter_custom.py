"""
Ask Ross Newsletter — Custom Image Builder
Produces a 1200 × 900 px PNG for Google My Business + Facebook.
Uses a user-supplied image as the hero banner — no API calls required.

Usage:
    python build_newsletter_custom.py \
        --banner-image "in/mark-carney.jpg" \
        --title1 "Mark Carney's Win: What It Means for Housing" \
        --intro "Canada has a new PM and housing is front and center..."

Requires:
    assets/ask-ross-overlay.png  (1200×900 RGBA transparent overlay)
    fonts/Aleo-Regular.ttf
    fonts/Aleo-Bold.ttf
    fonts/OpenSans-Regular.ttf
"""

import argparse
import os
from pathlib import Path
from textwrap import dedent

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
# Step 2 — load and crop user-supplied image
# ---------------------------------------------------------------------------

def load_banner(image_path: str) -> Image.Image:
    """Load any image and center-crop to 1200×638."""
    path = Path(image_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    if not path.exists():
        raise FileNotFoundError(
            f"Banner image not found: {path}\n"
            f"Drop your image into the 'in/' folder and pass the path with --banner-image."
        )
    img = Image.open(path).convert("RGB")
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
    banner_image: str,
    title1: str,
    title2: str,
    intro: str,
    output_path: str | None = None,
    reuse_banner: bool = False,
    banner_zoom: float = 1.0,
) -> None:
    stem = _title_to_filename(title1)
    out_dir = ROOT_DIR / "out"
    if output_path is None:
        output_path = str(out_dir / f"{stem} GMB Share.png")
    banner_cache = str(out_dir / f"{stem} Banner.png")
    os.makedirs(str(out_dir), exist_ok=True)

    print("Step 1: Creating canvas...")
    canvas = create_canvas()

    if reuse_banner and Path(banner_cache).exists():
        print("Step 2: Loading cached banner (skipping image load)...")
        banner = Image.open(banner_cache).convert("RGB")
    else:
        print(f"Step 2: Loading banner image: {banner_image}")
        banner = load_banner(banner_image)
        banner.save(banner_cache, "PNG", optimize=True)
        print(f"  Banner saved: {banner_cache}")

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
        description="Build an Ask Ross Newsletter social share image from a supplied photo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Examples:
              python build_newsletter_custom.py \\
                --banner-image "in/mark-carney.jpg" \\
                --title1 "Mark Carney's Win: What It Means for Housing" \\
                --intro "Canada has a new PM and housing is front and center..."

              # Adjust crop without reloading image
              python build_newsletter_custom.py \\
                --banner-image "in/mark-carney.jpg" \\
                --banner-zoom 1.2 --reuse-banner \\
                --title1 "..." --intro "..."
        """),
    )
    parser.add_argument("--banner-image", required=True,
                        help="Path to the image file (relative to script dir or absolute)")
    parser.add_argument("--title1", required=True,
                        help="Lead headline (max 55 chars)")
    parser.add_argument("--title2", default="| Ask Ross Newsletter")
    parser.add_argument("--intro", required=True,
                        help="2-3 sentence summary (max 245 chars, no em dashes)")
    parser.add_argument("--output", default=None,
                        help="Override output path (default: derived from title1)")
    parser.add_argument("--reuse-banner", action="store_true",
                        help="Skip image load, reuse cached Banner PNG from out/")
    parser.add_argument("--banner-zoom", type=float, default=1.0,
                        help="Zoom factor (1.0=none, 1.2=20%% closer, bottom-anchored)")

    args = parser.parse_args()
    build_newsletter(
        banner_image=args.banner_image,
        title1=args.title1,
        title2=args.title2,
        intro=args.intro,
        output_path=args.output,
        reuse_banner=args.reuse_banner,
        banner_zoom=args.banner_zoom,
    )


if __name__ == "__main__":
    main()
