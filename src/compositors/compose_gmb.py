"""
compose_gmb.py — Build Google My Business (GMB) share images for 4 cities (1200x900).

Each city overlay has embedded branding at y=456-686:
  AskRoss.ca logo, brand text, red accent bar, city name (pre-rendered per city)

After applying the overlay, the H1 article title is rendered in the title zone.

Output (in GMB subdir):
  Toronto - {article title}.png        1200x900
  Ottawa - {article title}.png         1200x900
  Richmond Hill - {article title}.png  1200x900
  Mississauga - {article title}.png    1200x900
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
)

CANVAS_W = 1200
CANVAS_H = 900

# Title text constants per RULES.md
GMB_TEXT_X       = 237   # left margin (aligns with embedded branding)
GMB_TEXT_Y       = 587   # below city name element (y≈544-558)
GMB_MAX_WIDTH    = 960   # 1200 - 237 - 3px right margin
GMB_LINE_HEIGHT  = 40
GMB_START_SIZE   = 34
GMB_MIN_SIZE     = 18
GMB_MAX_LINES    = 2

GMB_CITIES = ["Toronto", "Ottawa", "Richmond Hill", "Mississauga"]


def compose_gmb_image(
    title: str,
    city: str,
    background: Image.Image,
    overlay_path: str,
    font_path: str,
    out_dir: str,
    article_title_safe: str,
) -> tuple:
    """Build a single GMB image for one city. Returns (out_path, ok) tuple."""
    os.makedirs(out_dir, exist_ok=True)
    safe     = sanitize_filename(article_title_safe)
    out_path = os.path.join(out_dir, f"{city} - {safe}.png")

    print(f"\n  GMB {city}: {os.path.basename(out_path)}")

    # 1. Resize background to 1200x900
    canvas = resize_and_center_crop(background, CANVAS_W, CANVAS_H)

    # 2. Apply city overlay (embeds logo, brand text, red bar, city name)
    canvas = apply_overlay(canvas, overlay_path)

    # 3. Auto-fit Archivo Black for title
    font, lines = fit_font_size(
        text=title,
        font_path=font_path,
        max_width=GMB_MAX_WIDTH,
        max_lines=GMB_MAX_LINES,
        start_size=GMB_START_SIZE,
        min_size=GMB_MIN_SIZE,
    )
    print(f"    Title: {len(lines)} lines at {font.size}px")

    # 4. Render title with drop shadow
    canvas = draw_text_with_shadow(
        canvas=canvas,
        lines=lines,
        font=font,
        text_x=GMB_TEXT_X,
        text_y=GMB_TEXT_Y,
        line_height=GMB_LINE_HEIGHT,
        align="left",
    )

    # 5. Save
    save_rgb(canvas, out_path)
    ok = verify_dimensions(out_path, CANVAS_W, CANVAS_H)
    return (out_path, ok)


def compose_all_gmb_images(
    title: str,
    background: Image.Image,
    gmb_overlay_dir: str,
    font_path: str,
    out_dir: str,
    article_title_safe: str,
    cities: list = None,
) -> list:
    """Build GMB images for all cities. Returns list of (path, ok) tuples."""
    os.makedirs(out_dir, exist_ok=True)
    if cities is None:
        cities = GMB_CITIES

    results = []
    for city in cities:
        overlay_path = os.path.join(gmb_overlay_dir, f"{city} - Title.png")
        if not os.path.exists(overlay_path):
            print(f"  WARNING: GMB overlay not found for {city}: {overlay_path}")
            continue
        result = compose_gmb_image(
            title=title,
            city=city,
            background=background,
            overlay_path=overlay_path,
            font_path=font_path,
            out_dir=out_dir,
            article_title_safe=article_title_safe,
        )
        results.append(result)

    return results
