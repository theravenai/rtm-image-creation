"""
compose_feature.py — Build the Feature Image (700x450).

Produces two files:
  {title} - Feature Background RAW.png   700x450  (no overlay, no text — reusable asset)
  Feature Image - {title}.png            700x450  (overlay + two text layers)

Two text layers (rendered after overlay):
  Layer 1 — THEME (topic label)
    Font:     Aleo SemiBold, ALL CAPS, ~20px, 1px letter spacing
    Position: x=138, y=276

  Layer 2 — MAIN TITLE
    Font:     Open Sans Bold 700, ALL CAPS, 1px letter spacing, 1.3× line height
    Size:     auto-fit 35→14px (width + height constrained)
    Position: x=137, dynamically placed just below theme text
    Max width: 560px
    Overlay selected automatically based on actual wrap line count.
"""

import os

from PIL import Image, ImageFont

from .shared import (
    apply_overlay,
    draw_text_with_shadow,
    fit_font_size,
    prevent_widow,
    resize_and_center_crop,
    save_rgb,
    sanitize_filename,
    verify_dimensions,
    wrap_text,
)

CANVAS_W = 700
CANVAS_H = 450

# Theme text — Aleo SemiBold, ALL CAPS
THEME_X              = 138
THEME_Y              = 280
THEME_MAX_WIDTH      = 560
THEME_START_SIZE     = 13
THEME_MIN_SIZE       = 8
THEME_LETTER_SPACING = 1
THEME_LINE_GAP       = 6    # px between theme bottom and title top (title_y = 280+13+6 = 299)

# Title text — Open Sans Bold 700, ALL CAPS (same style as GMB template)
TITLE_X              = 138
TITLE_MAX_WIDTH      = 440  # forces "BEFORE" as line-1 break point at 20px Bold, 0px spacing
TITLE_START_SIZE     = 20   # user-specified target size
TITLE_MIN_SIZE       = 14
TITLE_MAX_LINES      = 3
TITLE_LETTER_SPACING = 0
TITLE_LINE_HEIGHT_RATIO = 1.3

# Bottom of the overlay text zone (top edge of bottom red bar) per overlay type
# Used to enforce a height budget so title never overflows the template.
TEXT_ZONE_BOTTOM_2LINE = 360
TEXT_ZONE_BOTTOM_3LINE = 390


def compose_feature_image(
    title: str,
    theme_label: str,
    background: Image.Image,
    overlay_2line_path: str,
    overlay_3line_path: str,
    aleo_font_path: str,
    opensans_font_path: str,
    out_dir: str,
    article_title_safe: str,
    title_line_count: int = None,  # ignored — overlay auto-selected from actual wrap
) -> list:
    """Build the feature image (700x450) and save the raw background.

    Args:
        title:              H1 article title text (will be uppercased for rendering).
        theme_label:        Short 2-4 word topic label (e.g. "Housing News").
        background:         Background PIL Image (any size).
        overlay_2line_path: Path to 2-line title overlay PNG.
        overlay_3line_path: Path to 3-line title overlay PNG.
        aleo_font_path:     Path to Aleo-SemiBold.ttf.
        opensans_font_path: Path to OpenSans-Bold.ttf.
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

    # 3. Fit theme first — its height determines where the title starts
    theme_upper = theme_label.upper()
    theme_font, theme_lines = fit_font_size(
        text=theme_upper,
        font_path=aleo_font_path,
        max_width=THEME_MAX_WIDTH,
        max_lines=1,
        start_size=THEME_START_SIZE,
        min_size=THEME_MIN_SIZE,
        letter_spacing=THEME_LETTER_SPACING,
    )
    title_y = THEME_Y + theme_font.size + THEME_LINE_GAP

    # 4. Fit title for width/line count
    title_upper = title.upper()
    title_font, title_lines = fit_font_size(
        text=title_upper,
        font_path=opensans_font_path,
        max_width=TITLE_MAX_WIDTH,
        max_lines=TITLE_MAX_LINES,
        start_size=TITLE_START_SIZE,
        min_size=TITLE_MIN_SIZE,
        letter_spacing=TITLE_LETTER_SPACING,
    )
    title_lines = prevent_widow(title_lines, title_font, TITLE_MAX_WIDTH, TITLE_LETTER_SPACING)
    actual_lines = len(title_lines)

    # 5. Apply height budget, then select overlay from final line count
    #    Loop once: budget may reduce line count → different overlay → slightly different budget
    for _pass in range(2):
        zone_bottom = TEXT_ZONE_BOTTOM_3LINE if actual_lines >= 3 else TEXT_ZONE_BOTTOM_2LINE
        available_h = zone_bottom - title_y - 4   # 4px safety margin
        max_size_h  = int(available_h / ((actual_lines - 1) * TITLE_LINE_HEIGHT_RATIO + 1))
        if title_font.size > max_size_h:
            title_font, title_lines = fit_font_size(
                text=title_upper,
                font_path=opensans_font_path,
                max_width=TITLE_MAX_WIDTH,
                max_lines=TITLE_MAX_LINES,
                start_size=max_size_h,
                min_size=TITLE_MIN_SIZE,
                letter_spacing=TITLE_LETTER_SPACING,
            )
            title_lines = prevent_widow(title_lines, title_font, TITLE_MAX_WIDTH, TITLE_LETTER_SPACING)
            actual_lines = len(title_lines)

    if actual_lines >= 3:
        overlay_path = overlay_3line_path
        print(f"    3-line overlay (actual lines={actual_lines})")
    else:
        overlay_path = overlay_2line_path
        print(f"    2-line overlay (actual lines={actual_lines})")

    # 6. Apply overlay
    canvas = apply_overlay(canvas, overlay_path)

    # 7. Theme text
    print(f"    Theme: '{theme_upper}' at {theme_font.size}px Aleo")
    canvas = draw_text_with_shadow(
        canvas=canvas,
        lines=theme_lines,
        font=theme_font,
        text_x=THEME_X,
        text_y=THEME_Y,
        line_height=theme_font.size + 4,
        align="left",
        letter_spacing=THEME_LETTER_SPACING,
    )

    # 8. Title text
    title_line_height = int(title_font.size * TITLE_LINE_HEIGHT_RATIO)
    print(f"    Title: {actual_lines} lines at {title_font.size}px Open Sans Bold, "
          f"line_height={title_line_height}px, title_y={title_y}")
    canvas = draw_text_with_shadow(
        canvas=canvas,
        lines=title_lines,
        font=title_font,
        text_x=TITLE_X,
        text_y=title_y,
        line_height=title_line_height,
        align="left",
        letter_spacing=TITLE_LETTER_SPACING,
    )

    # 9. Save final
    save_rgb(canvas, final_path)
    results.append((final_path, verify_dimensions(final_path, CANVAS_W, CANVAS_H)))

    return results
