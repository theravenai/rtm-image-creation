"""
compose_feature.py — Build the Feature Image (700x450).

Produces two files:
  {title} - Feature Background RAW.png   700x450  (no overlay, no text — reusable asset)
  Feature Image - {title}.png            700x450  (overlay + two text layers)

Two text layers (rendered after overlay):
  Layer 1 — THEME (topic label)
    Font:     Aleo SemiBold ~16px
    Position: x=138, y=276  (below logo/red-bar design element)
    Max width: 560px

  Layer 2 — MAIN TITLE
    Font:     Open Sans Bold, ALL CAPS
    Size:     auto-fit 28→14px
    Position: x=138, y=306 (2-line overlay) or y=286 (3-line overlay)
    Max width: 560px
    Line height: font_size + 10px
"""

import os

from PIL import Image, ImageFont

from .shared import (
    apply_overlay,
    draw_text_with_shadow,
    fit_font_size,
    resize_and_center_crop,
    save_rgb,
    sanitize_filename,
    verify_dimensions,
    wrap_text,
)

CANVAS_W = 700
CANVAS_H = 450

# Theme text — Aleo SemiBold
THEME_X         = 138
THEME_Y         = 276
THEME_MAX_WIDTH = 560
THEME_START_SIZE = 20
THEME_MIN_SIZE   = 12

# Title text — Open Sans ExtraBold, ALL CAPS
TITLE_X_2LINE   = 138
TITLE_Y_2LINE   = 303   # for 2-line overlay
TITLE_Y_3LINE   = 283   # for 3-line overlay (10px higher to accommodate extra line)
TITLE_MAX_WIDTH = 560
TITLE_START_SIZE = 28
TITLE_MIN_SIZE   = 14
TITLE_MAX_LINES  = 3    # never allow 4+ lines


def compose_feature_image(
    title: str,
    theme_label: str,
    title_line_count: int,
    background: Image.Image,
    overlay_2line_path: str,
    overlay_3line_path: str,
    aleo_font_path: str,
    opensans_font_path: str,
    out_dir: str,
    article_title_safe: str,
) -> list:
    """Build the feature image (700x450) and save the raw background.

    Args:
        title:              H1 article title text (will be uppercased for rendering).
        theme_label:        Short 2-4 word topic label (e.g. "Mortgage Rates").
        title_line_count:   Manifest value — 2 or 3, selects overlay.
        background:         Background PIL Image (any size).
        overlay_2line_path: Path to 2-line title overlay PNG.
        overlay_3line_path: Path to 3-line title overlay PNG.
        aleo_font_path:     Path to Aleo-SemiBold.ttf.
        opensans_font_path: Path to OpenSans-ExtraBold.ttf.
        out_dir:            Output directory.
        article_title_safe: Sanitized article title for filenames.

    Returns:
        List of (path, ok) tuples.
    """
    os.makedirs(out_dir, exist_ok=True)
    results = []

    safe = sanitize_filename(article_title_safe)
    raw_path   = os.path.join(out_dir, f"{safe} - Feature Background RAW.png")
    final_path = os.path.join(out_dir, f"Feature Image - {safe}.png")

    print(f"\n  Feature image: {os.path.basename(final_path)}")

    # 1. Resize background to 700x450
    canvas = resize_and_center_crop(background, CANVAS_W, CANVAS_H)

    # 2. Save RAW background (no overlay, no text)
    save_rgb(canvas, raw_path)
    results.append((raw_path, verify_dimensions(raw_path, CANVAS_W, CANVAS_H)))

    # 3. Select overlay based on line count
    if title_line_count >= 3:
        overlay_path = overlay_3line_path
        title_y      = TITLE_Y_3LINE
        print(f"    3-line overlay (title_line_count={title_line_count})")
    else:
        overlay_path = overlay_2line_path
        title_y      = TITLE_Y_2LINE
        print(f"    2-line overlay (title_line_count={title_line_count})")

    # 4. Apply overlay
    canvas = apply_overlay(canvas, overlay_path)

    # 5. Theme text — Aleo SemiBold, auto-fit to 1 line
    theme_font, theme_lines = fit_font_size(
        text=theme_label,
        font_path=aleo_font_path,
        max_width=THEME_MAX_WIDTH,
        max_lines=1,
        start_size=THEME_START_SIZE,
        min_size=THEME_MIN_SIZE,
    )
    print(f"    Theme: '{theme_label}' at {theme_font.size}px Aleo")
    canvas = draw_text_with_shadow(
        canvas=canvas,
        lines=theme_lines,
        font=theme_font,
        text_x=THEME_X,
        text_y=THEME_Y,
        line_height=theme_font.size + 4,
        align="left",
    )

    # 6. Title text — Open Sans ExtraBold, ALL CAPS
    title_upper = title.upper()
    title_font, title_lines = fit_font_size(
        text=title_upper,
        font_path=opensans_font_path,
        max_width=TITLE_MAX_WIDTH,
        max_lines=TITLE_MAX_LINES,
        start_size=TITLE_START_SIZE,
        min_size=TITLE_MIN_SIZE,
    )
    title_line_height = title_font.size + 10
    print(f"    Title: {len(title_lines)} lines at {title_font.size}px Open Sans ExtraBold")
    canvas = draw_text_with_shadow(
        canvas=canvas,
        lines=title_lines,
        font=title_font,
        text_x=TITLE_X_2LINE,
        text_y=title_y,
        line_height=title_line_height,
        align="left",
    )

    # 7. Save final
    save_rgb(canvas, final_path)
    results.append((final_path, verify_dimensions(final_path, CANVAS_W, CANVAS_H)))

    return results
