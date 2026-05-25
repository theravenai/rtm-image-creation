"""
compose_article_images.py — Build BLOG POST article images (1920x1080).

One image per H2 section:
  - Regular H2:    generated/solid background → standard overlay → Archivo Black 60px white title text
  - Bottom-line H2: reusable background → logo-only overlay → NO TEXT
  - FAQ H2:        reusable background → standard overlay → title text rendered

All saved to: out_dir/BLOG POST - Large Article Images for Askross.ca/
"""

import glob
import os
import random

from PIL import Image, ImageFont

from .shared import (
    apply_overlay,
    auto_text_position,
    draw_text_with_shadow,
    prevent_widow,
    resize_and_center_crop,
    save_rgb,
    wrap_text,
    verify_dimensions,
)

CANVAS_W = 1920
CANVAS_H = 1080

# Typography constants per RULES.md
FONT_SIZE          = 60
TEXT_LINE_HEIGHT   = 75    # 60px font + 15px leading
TEXT_LEFT_MARGIN   = 227   # just right of logo box (logo spans x=24-217)
TEXT_MAX_WIDTH_LEFT   = 1300  # upper-left and lower-left — wide enough for 2-line wrapping on most titles
TEXT_MAX_WIDTH_CENTER = 1400  # center — wide enough for 2-line wrapping on most titles

# Y positions per RULES.md
UPPER_LEFT_Y          = 284
LOWER_LEFT_BOTTOM_PAD = 189   # bottom padding; text_y ≈ 741 for 2 lines


def _pick_random_from_pool(pattern: str) -> str:
    """Return a random file path matching the glob pattern. Raises if none found."""
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No files matching pool pattern: {pattern}")
    return random.choice(matches)


def _lower_left_y(num_lines: int = 2) -> int:
    return CANVAS_H - LOWER_LEFT_BOTTOM_PAD - num_lines * TEXT_LINE_HEIGHT


def _center_y(num_lines: int = 2) -> int:
    return (CANVAS_H - num_lines * TEXT_LINE_HEIGHT) // 2


def _render_title(canvas: Image.Image, h2_text: str, font_path: str, force_position: str = None) -> Image.Image:
    """Run luminance analysis (or use force_position), wrap text, render with shadow."""
    position  = force_position if force_position else auto_text_position(canvas)
    font      = ImageFont.truetype(font_path, FONT_SIZE)

    if position == "center":
        max_width = TEXT_MAX_WIDTH_CENTER
        align     = "center"
    else:
        max_width = TEXT_MAX_WIDTH_LEFT
        align     = "left"

    lines = wrap_text(h2_text, font, max_width)
    lines = prevent_widow(lines, font, max_width)

    if position == "upper-left":
        text_x = TEXT_LEFT_MARGIN
        text_y = UPPER_LEFT_Y
    elif position == "lower-left":
        text_x = TEXT_LEFT_MARGIN
        text_y = _lower_left_y(len(lines))
    else:  # center
        text_x = TEXT_LEFT_MARGIN  # ignored when align='center'
        text_y = _center_y(len(lines))

    return draw_text_with_shadow(
        canvas=canvas,
        lines=lines,
        font=font,
        text_x=text_x,
        text_y=text_y,
        line_height=TEXT_LINE_HEIGHT,
        align=align,
    )


def compose_article_image(
    h2_text: str,
    background: Image.Image,
    overlay_path: str,
    font_path: str,
    out_path: str,
    force_position: str = None,
) -> bool:
    """Build a single 1920x1080 article image with text and overlay.

    force_position: 'upper-left', 'lower-left', or 'center'. If None, uses luminance analysis.
    """
    print(f"\n  Article image: {os.path.basename(out_path)}")

    canvas = resize_and_center_crop(background, CANVAS_W, CANVAS_H)
    canvas = apply_overlay(canvas, overlay_path)
    canvas = _render_title(canvas, h2_text, font_path, force_position=force_position)

    save_rgb(canvas, out_path)
    return verify_dimensions(out_path, CANVAS_W, CANVAS_H)


def compose_bottom_line_image(
    bottom_line_pool_pattern: str,
    overlay_path: str,
    out_path: str,
) -> bool:
    """Build bottom-line image: reusable bg + logo overlay. NO TEXT — ever."""
    print(f"\n  Bottom-line image: {os.path.basename(out_path)}")

    bg_path = _pick_random_from_pool(bottom_line_pool_pattern)
    print(f"    Pool image: {os.path.basename(bg_path)}")
    background = Image.open(bg_path).convert("RGB")

    canvas = resize_and_center_crop(background, CANVAS_W, CANVAS_H)
    canvas = apply_overlay(canvas, overlay_path)

    save_rgb(canvas, out_path)
    return verify_dimensions(out_path, CANVAS_W, CANVAS_H)


def compose_faq_image(
    faq_pool_pattern: str,
    out_path: str,
) -> bool:
    """Pick a FAQ pool image, resize to 1920x1080, save. No overlay, no text — ever."""
    print(f"\n  FAQ image: {os.path.basename(out_path)}")

    bg_path = _pick_random_from_pool(faq_pool_pattern)
    print(f"    Pool image: {os.path.basename(bg_path)}")
    background = Image.open(bg_path).convert("RGB")

    canvas = resize_and_center_crop(background, CANVAS_W, CANVAS_H)
    # No overlay, no text — pool images are the complete deliverable

    save_rgb(canvas, out_path)
    return verify_dimensions(out_path, CANVAS_W, CANVAS_H)


def compose_all_article_images(
    manifest: dict,
    article_bg: Image.Image,
    article_overlay_path: str,
    bottom_line_overlay_path: str,
    bottom_line_pool_pattern: str,
    faq_pool_pattern: str,
    font_path: str,
    out_subdir: str,
) -> list:
    """Build all article images for the manifest. Returns list of (path, ok) tuples."""
    os.makedirs(out_subdir, exist_ok=True)
    results = []

    for section in manifest["h2_sections"]:
        text     = section["text"]
        filename = section["filename"]
        out_path = os.path.join(out_subdir, filename)

        if section["is_bottom_line"]:
            ok = compose_bottom_line_image(
                bottom_line_pool_pattern=bottom_line_pool_pattern,
                overlay_path=bottom_line_overlay_path,
                out_path=out_path,
            )
        elif section["is_faq"]:
            ok = compose_faq_image(
                faq_pool_pattern=faq_pool_pattern,
                out_path=out_path,
            )
        else:
            ok = compose_article_image(
                h2_text=text,
                background=article_bg,
                overlay_path=article_overlay_path,
                font_path=font_path,
                out_path=out_path,
            )

        results.append((out_path, ok))

    return results
