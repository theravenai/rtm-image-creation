"""
generate_phase2.py — Generate real photo backgrounds for Phase 2 via Pexels.

Workflow:
  1. Reads out/manifest.json
  2. Fetches editorial photos from Pexels for each section
  3. Saves raw backgrounds to out/generated/
  4. Runs the full compositing pipeline

Usage:
  python generate_phase2.py

Requires:
  PEXELS_API_KEY in .env  (primary source)
  OPENROUTER_IMAGE_API_KEY in .env  (future AI generation; currently falls back to Pexels)

Output:
  out/generated/feature_bg.png              — shared background for feature/banner/GMB
  out/generated/{filename_base}.png         — per-H2 article backgrounds
  out/Blog Images - {title}/                — final composited images
"""

import glob as glob_mod
import io
import json
import os
import random
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

SCRIPT_DIR    = Path(__file__).parent.resolve()
REF_DIR       = SCRIPT_DIR / "references"
GENERATED_DIR = SCRIPT_DIR / "out" / "generated"

_HOME_FOR_SALE_POOL = str(
    REF_DIR / "BLOG POST - Large Article Images for Askross.ca"
    / "Reusable Image Large Article Image Assets" / "home for sale options" / "*.png"
)


def _is_selling_article(title: str) -> bool:
    low = title.lower()
    return any(kw in low for kw in ("sell", "selling", "for sale"))


def _load_env():
    local    = SCRIPT_DIR / ".env"
    fallback = REF_DIR / "(2) Newsletter Image Creation - Use for process creation reference" / ".env"
    if local.exists():
        load_dotenv(local)
    elif fallback.exists():
        load_dotenv(fallback)


# ---------------------------------------------------------------------------
# Pexels image fetcher
# ---------------------------------------------------------------------------

PEXELS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _pexels_search(query: str, api_key: str, count: int = 5) -> list:
    """Return list of landscape photo dicts from Pexels."""
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": count, "orientation": "landscape"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("photos", [])


def _download_pexels_photo(photo: dict) -> Image.Image:
    """Download a Pexels photo at large2x resolution."""
    url = photo["src"]["large2x"]
    r = requests.get(url, timeout=30, headers=PEXELS_HEADERS)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def _fetch_pexels(query: str, api_key: str, label: str) -> Image.Image:
    """Fetch best landscape photo from Pexels for a query. Returns PIL Image."""
    print(f"  Fetching Pexels: '{query}' ({label})")
    photos = _pexels_search(query, api_key, count=8)
    if not photos:
        raise RuntimeError(f"No Pexels photos for '{query}'")

    # Prefer wider photos (≥1.7 ratio)
    best = None
    for ph in photos:
        ratio = ph["width"] / ph["height"]
        if ratio >= 1.7:
            best = ph
            break
    if best is None:
        best = photos[0]

    img = _download_pexels_photo(best)
    print(f"  Got: {img.width}x{img.height} — {best['photographer']}")
    return img


# ---------------------------------------------------------------------------
# Section-to-Pexels query mapping
# ---------------------------------------------------------------------------

def _pexels_query_for_feature(title: str) -> str:
    """Pexels query for feature bg — only called for non-selling articles."""
    low = title.lower()
    if "bank of canada" in low or "rate" in low:
        return "Bank of Canada Ottawa building"
    if "renewal" in low or "payment shock" in low:
        return "mortgage document kitchen"
    if "equity" in low or "underwater" in low:
        return "house model piggy bank"
    return "Canadian neighbourhood homes street"


def _pexels_query_for_section(section: dict) -> str:
    """Simple, targeted Pexels search terms — 3-4 words max for best results."""
    text = section.get("text", "").lower()

    if "actually happening" in text or "right now" in text:
        return "couple worried mortgage documents"
    if "renewal" in text and ("worse" in text or "mortgage" in text):
        return "mortgage renewal letter calendar"
    if "equity" in text or "underwater" in text:
        return "house model piggy bank"
    if "warning" in text or "forced sale" in text:
        return "foreclosure sign house yard"
    if "waiting" in text or "market" in text and "recover" in text:
        return "hourglass calendar time"
    if "credit" in text:
        return "credit score laptop"
    if "reset" in text or "fresh start" in text:
        return "couple laptop financial planning"
    return "Canadian home real estate"


def _pexels_query_for_bottom_line(manifest: dict) -> str:
    """Bottom-line uses home for sale pool for selling articles; otherwise Pexels."""
    low = manifest.get("title", "").lower()
    if "sell" in low or "selling" in low or "for sale" in low:
        return None  # caller will use home for sale pool
    if "renewal" in low or "payment shock" in low:
        return "mortgage advisor couple office"
    return "mortgage advisor professional office"


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------

def _save(img: Image.Image, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path, "PNG")
    print(f"  Saved: {os.path.basename(path)} ({img.width}x{img.height})")


# ---------------------------------------------------------------------------
# Main Phase 2 workflow
# ---------------------------------------------------------------------------

def run_phase2():
    _load_env()

    print("\n=== Phase 2: Background Generation (Pexels) ===")

    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    if not pexels_key:
        raise EnvironmentError("PEXELS_API_KEY not set in .env")
    print(f"  Pexels API key loaded (length={len(pexels_key)})")

    # Load manifest
    manifest_path = SCRIPT_DIR / "out" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"  Manifest: '{manifest['title']}' ({len(manifest['h2_sections'])} sections)")

    os.makedirs(GENERATED_DIR, exist_ok=True)

    # -----------------------------------------------------------------------
    # 1. Feature background (shared by feature image, banners, GMB)
    # -----------------------------------------------------------------------
    print("\n[1] Feature / Banner / GMB background")
    feature_bg_path = str(GENERATED_DIR / "feature_bg.png")

    if _is_selling_article(manifest["title"]):
        # Selling articles: always use the prebuilt home for sale pool
        pool_files = glob_mod.glob(_HOME_FOR_SALE_POOL)
        if not pool_files:
            raise FileNotFoundError(f"No images found in home for sale pool: {_HOME_FOR_SALE_POOL}")
        chosen = random.choice(pool_files)
        print(f"  Selling article — using home for sale pool: {os.path.basename(chosen)}")
        feature_bg = Image.open(chosen).convert("RGB")
        _save(feature_bg, feature_bg_path)
    elif Path(feature_bg_path).exists():
        print(f"  Reusing cached: {feature_bg_path}")
        feature_bg = Image.open(feature_bg_path).convert("RGB")
    else:
        feature_query = _pexels_query_for_feature(manifest["title"])
        feature_bg = _fetch_pexels(feature_query, pexels_key, "feature background")
        _save(feature_bg, feature_bg_path)
        time.sleep(1)

    # -----------------------------------------------------------------------
    # 2. Per-H2 article backgrounds
    # -----------------------------------------------------------------------
    print("\n[2] Article section backgrounds")

    from src.prompts.prompt_builder import build_all_prompts
    section_prompts = build_all_prompts(manifest)

    article_bgs = {}  # section_number -> PIL Image

    for entry in section_prompts:
        sec_num  = entry["section_number"]
        filename = entry["filename"]
        prompt   = entry["prompt"]

        section = next(
            (s for s in manifest["h2_sections"] if s["section_number"] == sec_num), {}
        )
        base     = filename.replace(".png", "")
        out_path = str(GENERATED_DIR / f"{base}.png")

        if section.get("is_bottom_line"):
            query = _pexels_query_for_bottom_line(manifest)
            if query is None:
                # Selling article — use home for sale pool for bottom-line too
                print(f"  Section {sec_num} (bottom-line): using home for sale pool")
                continue
        elif section.get("is_faq"):
            # FAQ always uses the reusable pool images — never fetch or generate
            print(f"  Section {sec_num}: FAQ — using pool image (no fetch)")
            continue
        elif prompt is None:
            print(f"  Section {sec_num}: skipped")
            continue
        else:
            query = _pexels_query_for_section(section)

        if Path(out_path).exists():
            print(f"  Section {sec_num}: reusing cached {os.path.basename(out_path)}")
            article_bgs[sec_num] = Image.open(out_path).convert("RGB")
            continue

        print(f"\n  Section {sec_num}: {section.get('text', '')[:60]}")
        img = _fetch_pexels(query, pexels_key, f"section {sec_num}")
        _save(img, out_path)
        article_bgs[sec_num] = img
        time.sleep(1)

    # -----------------------------------------------------------------------
    # 3. Composite all images
    # -----------------------------------------------------------------------
    print("\n[3] Running compositing pipeline...")
    _composite_phase2(manifest, feature_bg, article_bgs)

    print("\n=== Phase 2 complete ===")


def _composite_phase2(manifest: dict, feature_bg: Image.Image, article_bgs: dict):
    """Run full compositing pipeline with generated/fetched backgrounds."""
    from src.compositors.create_folder_structure import create_output_folder_structure
    from src.compositors.compose_article_images import (
        compose_article_image,
        compose_bottom_line_image,
        compose_faq_image,
    )
    from src.compositors.compose_feature import compose_feature_image
    from src.compositors.compose_banners import compose_all_banners
    from src.compositors.compose_gmb import compose_all_gmb_images
    from src.compositors.shared import sanitize_filename
    from run import _derive_theme_label

    # Asset paths
    article_overlay       = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "(1) AskRoss.ca - Just logo and grey overlay.png")
    bottom_line_overlay   = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "(8) Rule - AskRoss.ca - For The Closer - No Overlay - Just Logo.png")
    bottom_line_pool      = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "Reusable Image Large Article Image Assets" / "AskRoss.ca - Bottom line or Advice from Ross Taylor Mortgages*.png")
    faq_pool              = str(REF_DIR / "BLOG POST - Large Article Images for Askross.ca" / "Reusable Image Large Article Image Assets" / "AskRoss.ca - All of the FAQs in this article*.png")
    feature_overlay_2line = str(REF_DIR / "BLOG POST - Feature Image" / "Feature image - Use this is title is two lines - overlay.png")
    feature_overlay_3line = str(REF_DIR / "BLOG POST - Feature Image" / "Feature image - use this if title is three lines - overlay.png")
    desktop_overlay       = str(REF_DIR / "BLOG POST - Banner Images" / "Banner - Title of Article - Overlay.png")
    mobile_overlay        = str(REF_DIR / "BLOG POST - Banner Images" / "MOBILE - Title of Article - Overlay.png")
    gmb_overlay_dir       = str(REF_DIR / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE")
    font_archivo          = str(REF_DIR / "(2) Newsletter Image Creation - Use for process creation reference" / "(1) Banner Images" / "fonts" / "Archivo_Black" / "ArchivoBlack-Regular.ttf")
    font_aleo             = str(SCRIPT_DIR / "fonts" / "Aleo" / "static" / "Aleo-Bold.ttf")
    font_opensans         = str(SCRIPT_DIR / "fonts" / "Open_Sans" / "static" / "OpenSans-Regular.ttf")
    font_opensans_bold    = str(SCRIPT_DIR / "fonts" / "Open_Sans" / "static" / "OpenSans-Bold.ttf")

    article_title    = manifest["title"]
    title_line_count = manifest.get("title_line_count", 2)
    safe_title       = sanitize_filename(article_title)
    theme_label      = _derive_theme_label(manifest)

    dirs               = create_output_folder_structure(str(SCRIPT_DIR / "out"), article_title)
    root_dir           = dirs["root"]
    article_images_dir = dirs["article_images"]
    gmb_dir            = dirs["gmb"]

    # Article images — each section uses its own background
    print("\n  Article images...")
    for section in manifest["h2_sections"]:
        text     = section["text"]
        filename = section["filename"]
        sec_num  = section["section_number"]
        out_path = os.path.join(article_images_dir, filename)

        if section["is_bottom_line"]:
            bg = article_bgs.get(sec_num)
            if bg is not None:
                from src.compositors.shared import resize_and_center_crop, apply_overlay, save_rgb, verify_dimensions
                canvas = resize_and_center_crop(bg, 1920, 1080)
                canvas = apply_overlay(canvas, bottom_line_overlay)
                save_rgb(canvas, out_path)
                verify_dimensions(out_path, 1920, 1080)
                print(f"\n  Bottom-line (Pexels bg): {os.path.basename(out_path)}")
            elif _is_selling_article(manifest.get("title", "")):
                # Selling article — use home for sale pool for bottom-line
                pool_files = glob_mod.glob(_HOME_FOR_SALE_POOL)
                if pool_files:
                    chosen = random.choice(pool_files)
                    from src.compositors.shared import resize_and_center_crop, apply_overlay, save_rgb, verify_dimensions
                    bg_pool = Image.open(chosen).convert("RGB")
                    canvas = resize_and_center_crop(bg_pool, 1920, 1080)
                    canvas = apply_overlay(canvas, bottom_line_overlay)
                    save_rgb(canvas, out_path)
                    verify_dimensions(out_path, 1920, 1080)
                    print(f"\n  Bottom-line (home for sale pool): {os.path.basename(out_path)}")
            else:
                compose_bottom_line_image(
                    bottom_line_pool_pattern=bottom_line_pool,
                    overlay_path=bottom_line_overlay,
                    out_path=out_path,
                )
        elif section["is_faq"]:
            compose_faq_image(
                faq_pool_pattern=faq_pool,
                out_path=out_path,
            )
        else:
            bg = article_bgs.get(sec_num, feature_bg)
            compose_article_image(
                h2_text=text,
                background=bg,
                overlay_path=article_overlay,
                font_path=font_archivo,
                out_path=out_path,
            )

    # Feature image
    print("\n  Feature image...")
    compose_feature_image(
        title=article_title,
        theme_label=theme_label,
        title_line_count=title_line_count,
        background=feature_bg,
        overlay_2line_path=feature_overlay_2line,
        overlay_3line_path=feature_overlay_3line,
        aleo_font_path=font_aleo,
        opensans_font_path=font_opensans_bold,
        out_dir=root_dir,
        article_title_safe=safe_title,
    )

    # Banners
    print("\n  Banner images...")
    compose_all_banners(
        background=feature_bg,
        desktop_overlay_path=desktop_overlay,
        mobile_overlay_path=mobile_overlay,
        out_dir=root_dir,
        article_title_safe=safe_title,
    )

    # GMB images
    print("\n  GMB images...")
    gmb_cities = manifest.get("gmb_locations", ["Toronto", "Ottawa", "Richmond Hill", "Mississauga"])
    compose_all_gmb_images(
        title=article_title,
        background=feature_bg,
        gmb_overlay_dir=gmb_overlay_dir,
        font_path=font_opensans_bold,
        out_dir=gmb_dir,
        article_title_safe=safe_title,
        cities=gmb_cities,
    )

    print(f"\n  Output: {root_dir}")


if __name__ == "__main__":
    run_phase2()
