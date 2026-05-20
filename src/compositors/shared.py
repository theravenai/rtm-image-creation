"""
shared.py — Reusable compositing utilities for AskRoss.ca blog image pipeline.

Adapted from the newsletter banner process in:
  references/(2) Newsletter Image Creation.../build_newsletter_banner.py
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Drop shadow constants (same as newsletter script)
# ---------------------------------------------------------------------------
SHADOW_OFFSET  = 1    # 1px right + 1px down
SHADOW_BLUR    = 3    # GaussianBlur radius 3 (= Photoshop Size 6px)
SHADOW_OPACITY = 114  # 45% of 255


# ---------------------------------------------------------------------------
# Resize / crop
# ---------------------------------------------------------------------------

def resize_and_center_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Scale img to fill target dimensions then center-crop to exact size."""
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
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


# ---------------------------------------------------------------------------
# Overlay compositing
# ---------------------------------------------------------------------------

def apply_overlay(canvas: Image.Image, overlay_path: str) -> Image.Image:
    """Alpha-composite an RGBA overlay PNG on top of canvas. Returns RGBA image."""
    overlay = Image.open(overlay_path).convert("RGBA")
    if overlay.size != canvas.size:
        overlay = overlay.resize(canvas.size, Image.LANCZOS)
    return Image.alpha_composite(canvas.convert("RGBA"), overlay)


# ---------------------------------------------------------------------------
# Text wrapping
# ---------------------------------------------------------------------------

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """Word-wrap text to fit within max_width pixels. Returns list of lines."""
    words = text.split()
    lines = []
    current = []
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


# ---------------------------------------------------------------------------
# Font auto-sizing
# ---------------------------------------------------------------------------

def fit_font_size(
    text: str,
    font_path: str,
    max_width: int,
    max_lines: int = 3,
    start_size: int = 28,
    min_size: int = 12,
) -> tuple:
    """Reduce font size until text wraps to at most max_lines within max_width.

    Returns (font, lines) tuple where lines is the wrapped text at chosen size.
    """
    for size in range(start_size, min_size - 1, -1):
        font = ImageFont.truetype(font_path, size)
        lines = wrap_text(text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    font = ImageFont.truetype(font_path, min_size)
    lines = wrap_text(text, font, max_width)
    return font, lines


# ---------------------------------------------------------------------------
# Text rendering with drop shadow
# ---------------------------------------------------------------------------

def draw_text_with_shadow(
    canvas: Image.Image,
    lines: list,
    font: ImageFont.FreeTypeFont,
    text_x: int,
    text_y: int,
    line_height: int,
    align: str = "left",
    text_color: tuple = (255, 255, 255, 255),
    shadow_offset: int = SHADOW_OFFSET,
    shadow_blur: int = SHADOW_BLUR,
    shadow_opacity: int = SHADOW_OPACITY,
) -> Image.Image:
    """Draw pre-wrapped lines with drop shadow on canvas. Returns RGBA image.

    Args:
        canvas:     RGBA or RGB canvas to draw on.
        lines:      List of text lines (already wrapped).
        font:       FreeType font object.
        text_x:     Left margin for left-aligned text (ignored for center).
        text_y:     Top of first text line.
        line_height: Pixels between line tops (font_size + leading).
        align:      'left' or 'center'.
    """
    canvas_w, canvas_h = canvas.size

    shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow_draw  = ImageDraw.Draw(shadow_layer)

    for i, line in enumerate(lines):
        ly = text_y + i * line_height
        if align == "center":
            bb = font.getbbox(line)
            lx = (canvas_w - (bb[2] - bb[0])) // 2
        else:
            lx = text_x
        shadow_draw.text(
            (lx + shadow_offset, ly + shadow_offset),
            line,
            font=font,
            fill=(0, 0, 0, shadow_opacity),
        )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

    result = Image.alpha_composite(canvas.convert("RGBA"), shadow_layer)
    text_draw = ImageDraw.Draw(result)
    for i, line in enumerate(lines):
        ly = text_y + i * line_height
        if align == "center":
            bb = font.getbbox(line)
            lx = (canvas_w - (bb[2] - bb[0])) // 2
        else:
            lx = text_x
        text_draw.text((lx, ly), line, font=font, fill=text_color)

    return result


# ---------------------------------------------------------------------------
# Auto text position — luminance analysis (adapted from newsletter script)
# ---------------------------------------------------------------------------

def auto_text_position(canvas: Image.Image) -> str:
    """Return 'upper-left', 'lower-left', or 'center' for 1920x1080 article images.

    Picks the zone with the darkest average luminance (best contrast for white text).
    Zones are aligned to the RULES.md text position constants.
    """
    try:
        import numpy as np

        arr = np.array(canvas.convert("RGB")).astype(float)

        def lum(x1, y1, x2, y2):
            region = arr[y1:y2, x1:x2]
            if region.size == 0:
                return 255.0
            return (
                0.299 * region[:, :, 0]
                + 0.587 * region[:, :, 1]
                + 0.114 * region[:, :, 2]
            ).mean()

        # Zone extents match RULES.md constants for 1920x1080
        left_x  = 227   # TEXT_LEFT_MARGIN
        text_w  = 1000  # representative width for sampling
        line_h  = 75    # TEXT_LINE_HEIGHT
        num_lines = 2   # assume 2 lines for zone sizing

        upper_y = 284                           # UPPER_LEFT_Y
        lower_y = 1080 - 189 - num_lines * line_h  # ≈741
        center_y = (1080 - num_lines * line_h) // 2  # ≈465

        scores = {
            "upper-left": lum(left_x, upper_y, left_x + text_w, upper_y + num_lines * line_h),
            "lower-left": lum(left_x, lower_y, left_x + text_w, lower_y + num_lines * line_h),
            "center":     lum(left_x, center_y, left_x + text_w, center_y + num_lines * line_h),
        }
        best = min(scores, key=scores.get)
        print(
            f"  Auto text position: '{best}' "
            f"(lum — upper:{scores['upper-left']:.0f} "
            f"lower:{scores['lower-left']:.0f} "
            f"center:{scores['center']:.0f})"
        )
        return best
    except ImportError:
        print("  numpy not available — defaulting to lower-left")
        return "lower-left"


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def save_rgb(img: Image.Image, path: str) -> None:
    """Flatten RGBA to RGB (black matte) and save as PNG. Creates parent dirs."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (0, 0, 0))
        bg.paste(img, mask=img.split()[3])
        img = bg
    img.save(path, "PNG", optimize=True)
    print(f"  Saved: {os.path.basename(path)} ({img.width}x{img.height})")


def verify_dimensions(path: str, expected_w: int, expected_h: int) -> bool:
    """Open saved file and check exact dimensions. Returns True if correct."""
    img = Image.open(path)
    ok = img.size == (expected_w, expected_h)
    if not ok:
        print(f"  FAIL dimensions: {os.path.basename(path)} — got {img.size}, expected ({expected_w},{expected_h})")
    return ok


# ---------------------------------------------------------------------------
# Filename sanitization
# ---------------------------------------------------------------------------

def sanitize_filename(text: str) -> str:
    """Make H2 text safe for use in a Windows filename.

    Rules per RULES.md:
    - Remove trailing ? and !
    - Replace ': ' with '_ ' (colon-space → underscore-space)
    - Replace ':' with '_' (bare colon → underscore)
    - Remove ", *, \\, /, <, >, |
    - Strip leading/trailing whitespace
    - Preserve apostrophes
    """
    text = text.rstrip("?!")
    text = text.replace(": ", "_ ")
    text = text.replace(":", "_")
    for ch in '"*\\/<>|':
        text = text.replace(ch, "")
    return text.strip()
