"""
compose_banners.py — Build Desktop (1286x300) and Mobile (400x600) banner images.

RULE: Banner and mobile images NEVER have text rendered on them — ever.
The overlay provides the scrim; the photograph communicates the content.

Output:
  Banner - {article title}.png    (1286x300)
  Mobile - {article title}.png    (400x600)
"""

import os

from PIL import Image

from .shared import (
    apply_overlay,
    resize_and_center_crop,
    save_rgb,
    sanitize_filename,
    verify_dimensions,
)

DESKTOP_W = 1286
DESKTOP_H = 300

MOBILE_W = 400
MOBILE_H = 600


def compose_desktop_banner(
    background: Image.Image,
    overlay_path: str,
    out_dir: str,
    article_title_safe: str,
) -> tuple:
    """Build the 1286x300 desktop banner. Photo + overlay only — no text."""
    os.makedirs(out_dir, exist_ok=True)
    safe     = sanitize_filename(article_title_safe)
    out_path = os.path.join(out_dir, f"Banner - {safe}.png")

    print(f"\n  Desktop banner: {os.path.basename(out_path)}")

    canvas = resize_and_center_crop(background, DESKTOP_W, DESKTOP_H)
    canvas = apply_overlay(canvas, overlay_path)

    save_rgb(canvas, out_path)
    ok = verify_dimensions(out_path, DESKTOP_W, DESKTOP_H)
    return (out_path, ok)


def compose_mobile_banner(
    background: Image.Image,
    overlay_path: str,
    out_dir: str,
    article_title_safe: str,
) -> tuple:
    """Build the 400x600 mobile banner. Photo + overlay only — no text."""
    os.makedirs(out_dir, exist_ok=True)
    safe     = sanitize_filename(article_title_safe)
    out_path = os.path.join(out_dir, f"Mobile - {safe}.png")

    print(f"\n  Mobile banner: {os.path.basename(out_path)}")

    canvas = resize_and_center_crop(background, MOBILE_W, MOBILE_H)
    canvas = apply_overlay(canvas, overlay_path)

    save_rgb(canvas, out_path)
    ok = verify_dimensions(out_path, MOBILE_W, MOBILE_H)
    return (out_path, ok)


def compose_all_banners(
    background: Image.Image,
    desktop_overlay_path: str,
    mobile_overlay_path: str,
    out_dir: str,
    article_title_safe: str,
) -> list:
    """Build both desktop and mobile banners. Returns list of (path, ok) tuples."""
    results = []
    results.append(
        compose_desktop_banner(
            background=background,
            overlay_path=desktop_overlay_path,
            out_dir=out_dir,
            article_title_safe=article_title_safe,
        )
    )
    results.append(
        compose_mobile_banner(
            background=background,
            overlay_path=mobile_overlay_path,
            out_dir=out_dir,
            article_title_safe=article_title_safe,
        )
    )
    return results
