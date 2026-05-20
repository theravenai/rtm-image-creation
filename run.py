"""
run.py — AskRoss.ca Blog Image Creation Pipeline Entry Point.

Usage:
  # Phase 1 — test with solid-color backgrounds (no API calls)
  python run.py --article "Should You Sell Your Home Before Things Get Worse.md" --phase1

  # Phase 2 — generate real AI backgrounds via OpenRouter/Gemini
  python run.py --article "Should You Sell Your Home Before Things Get Worse.md" --phase2
"""

import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).parent.resolve()
REF_DIR    = SCRIPT_DIR / "references"


def _load_env():
    """Load .env from working directory root, with fallback to newsletter reference dir."""
    try:
        from dotenv import load_dotenv
        local_env    = SCRIPT_DIR / ".env"
        fallback_env = (
            REF_DIR
            / "(2) Newsletter Image Creation - Use for process creation reference"
            / ".env"
        )
        if local_env.exists():
            load_dotenv(local_env)
            print(f"  Loaded .env from: {local_env}")
        elif fallback_env.exists():
            load_dotenv(fallback_env)
            print(f"  Loaded .env from fallback: {fallback_env}")
        else:
            print("  No .env file found — API keys must be set in environment.")
    except ImportError:
        print("  python-dotenv not installed — skipping .env load.")


# ---------------------------------------------------------------------------
# Asset paths — all overlays/templates under references/
# ---------------------------------------------------------------------------

ASSET_PATHS = {
    # Article image overlays
    "article_overlay": (
        REF_DIR
        / "BLOG POST - Large Article Images for Askross.ca"
        / "(1) AskRoss.ca - Just logo and grey overlay.png"
    ),
    "bottom_line_overlay": (
        REF_DIR
        / "BLOG POST - Large Article Images for Askross.ca"
        / "(8) Rule - AskRoss.ca - For The Closer - No Overlay - Just Logo.png"
    ),
    "bottom_line_pool_pattern": str(
        REF_DIR
        / "BLOG POST - Large Article Images for Askross.ca"
        / "Reusable Image Large Article Image Assets"
        / "AskRoss.ca - Bottom line or Advice from Ross Taylor Mortgages*.png"
    ),
    "faq_pool_pattern": str(
        REF_DIR
        / "BLOG POST - Large Article Images for Askross.ca"
        / "Reusable Image Large Article Image Assets"
        / "AskRoss.ca - All of the FAQs in this article*.png"
    ),
    # Feature image overlays
    "feature_overlay_2line": (
        REF_DIR
        / "BLOG POST - Feature Image"
        / "Feature image - Use this is title is two lines - overlay.png"
    ),
    "feature_overlay_3line": (
        REF_DIR
        / "BLOG POST - Feature Image"
        / "Feature image - use this if title is three lines - overlay.png"
    ),
    # Banner overlays
    "desktop_banner_overlay": (
        REF_DIR
        / "BLOG POST - Banner Images"
        / "Banner - Title of Article - Overlay.png"
    ),
    "mobile_banner_overlay": (
        REF_DIR
        / "BLOG POST - Banner Images"
        / "MOBILE - Title of Article - Overlay.png"
    ),
    # GMB overlays directory
    "gmb_overlay_dir": (
        REF_DIR / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE"
    ),
    # Fonts
    "font_archivo": (
        REF_DIR
        / "(2) Newsletter Image Creation - Use for process creation reference"
        / "(1) Banner Images"
        / "fonts"
        / "Archivo_Black"
        / "ArchivoBlack-Regular.ttf"
    ),
    "font_aleo": (
        SCRIPT_DIR / "fonts" / "Aleo" / "static" / "Aleo-SemiBold.ttf"
    ),
    "font_opensans": (
        SCRIPT_DIR / "fonts" / "Open_Sans" / "static" / "OpenSans-SemiBold.ttf"
    ),
    # Manifest
    "manifest": SCRIPT_DIR / "out" / "manifest.json",
}


def _verify_assets():
    """Check that all required asset files/dirs exist. Returns True if all found."""
    required = [
        "article_overlay",
        "bottom_line_overlay",
        "feature_overlay_2line",
        "feature_overlay_3line",
        "desktop_banner_overlay",
        "mobile_banner_overlay",
        "gmb_overlay_dir",
        "font_archivo",
        "font_aleo",
        "font_opensans",
        "manifest",
    ]
    missing = []
    for key in required:
        p = Path(ASSET_PATHS[key])
        if not p.exists():
            missing.append(f"  MISSING [{key}]: {p}")
    if missing:
        print("Asset check FAILED:")
        for m in missing:
            print(m)
        return False
    print("  All required assets found.")
    return True


def _load_manifest() -> dict:
    manifest_path = ASSET_PATHS["manifest"]
    if not Path(manifest_path).exists():
        raise FileNotFoundError(
            f"Manifest not found at {manifest_path}. Run the parser first."
        )
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"  Manifest: '{manifest['title']}' ({len(manifest['h2_sections'])} sections)")
    return manifest


# ---------------------------------------------------------------------------
# Phase 1: solid-color test backgrounds
# ---------------------------------------------------------------------------

PHASE1_ARTICLE_BG_COLOR = (80, 90, 100)
PHASE1_FEATURE_BG_COLOR = (70, 80, 95)


def _solid_bg(color: tuple, size: tuple = (1920, 1080)) -> Image.Image:
    return Image.new("RGB", size, color)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(phase: int, output_base: str = None) -> None:
    _load_env()

    print("\n=== AskRoss.ca Blog Image Pipeline ===")
    print(f"  Phase: {phase}")

    print("\n[1/6] Verifying assets...")
    if not _verify_assets():
        sys.exit(1)

    print("\n[2/6] Loading manifest...")
    manifest        = _load_manifest()
    article_title   = manifest["title"]
    title_line_count = manifest.get("title_line_count", 2)

    # Build a short theme label from the article title for the feature image
    # (first 2-3 meaningful words)
    theme_label = _derive_theme_label(article_title)
    print(f"  Theme label: '{theme_label}'")

    if output_base:
        base_out = output_base
    elif phase == 1:
        base_out = str(SCRIPT_DIR / "out" / "test-output")
    else:
        base_out = str(SCRIPT_DIR / "out")

    from src.compositors.create_folder_structure import create_output_folder_structure
    from src.compositors.compose_article_images import compose_all_article_images
    from src.compositors.compose_feature import compose_feature_image
    from src.compositors.compose_banners import compose_all_banners
    from src.compositors.compose_gmb import compose_all_gmb_images
    from src.compositors.shared import sanitize_filename

    print("\n[3/6] Creating output folder structure...")
    dirs = create_output_folder_structure(base_out, article_title)
    root_dir         = dirs["root"]
    article_images_dir = dirs["article_images"]
    gmb_dir          = dirs["gmb"]

    print("\n[4/6] Preparing backgrounds...")
    if phase == 1:
        print("  Phase 1: using solid-color backgrounds")
        article_bg = _solid_bg(PHASE1_ARTICLE_BG_COLOR)
        feature_bg = _solid_bg(PHASE1_FEATURE_BG_COLOR)
    else:
        raise NotImplementedError(
            "Phase 2 backgrounds are generated via OpenRouter/Gemini. "
            "Run generate_backgrounds.py first, then pass --phase2 with --feature-bg."
        )

    all_results = []

    print("\n[5a/6] Building article images...")
    article_results = compose_all_article_images(
        manifest=manifest,
        article_bg=article_bg,
        article_overlay_path=str(ASSET_PATHS["article_overlay"]),
        bottom_line_overlay_path=str(ASSET_PATHS["bottom_line_overlay"]),
        bottom_line_pool_pattern=ASSET_PATHS["bottom_line_pool_pattern"],
        faq_pool_pattern=ASSET_PATHS["faq_pool_pattern"],
        font_path=str(ASSET_PATHS["font_archivo"]),
        out_subdir=article_images_dir,
    )
    all_results.extend(article_results)

    print("\n[5b/6] Building feature image...")
    safe_title = sanitize_filename(article_title)
    feature_results = compose_feature_image(
        title=article_title,
        theme_label=theme_label,
        title_line_count=title_line_count,
        background=feature_bg,
        overlay_2line_path=str(ASSET_PATHS["feature_overlay_2line"]),
        overlay_3line_path=str(ASSET_PATHS["feature_overlay_3line"]),
        aleo_font_path=str(ASSET_PATHS["font_aleo"]),
        opensans_font_path=str(ASSET_PATHS["font_opensans"]),
        out_dir=root_dir,
        article_title_safe=safe_title,
    )
    all_results.extend(feature_results)

    print("\n[5c/6] Building banner images...")
    banner_results = compose_all_banners(
        background=feature_bg,
        desktop_overlay_path=str(ASSET_PATHS["desktop_banner_overlay"]),
        mobile_overlay_path=str(ASSET_PATHS["mobile_banner_overlay"]),
        out_dir=root_dir,
        article_title_safe=safe_title,
    )
    all_results.extend(banner_results)

    print("\n[5d/6] Building GMB images...")
    gmb_cities  = manifest.get("gmb_locations", ["Toronto", "Ottawa", "Richmond Hill", "Mississauga"])
    gmb_results = compose_all_gmb_images(
        title=article_title,
        background=feature_bg,
        gmb_overlay_dir=str(ASSET_PATHS["gmb_overlay_dir"]),
        font_path=str(ASSET_PATHS["font_archivo"]),
        out_dir=gmb_dir,
        article_title_safe=safe_title,
        cities=gmb_cities,
    )
    all_results.extend(gmb_results)

    print("\n[6/6] Results summary...")
    failed = [(p, ok) for p, ok in all_results if not ok]
    passed = [(p, ok) for p, ok in all_results if ok]

    print(f"\n  Total files: {len(all_results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    for p, ok in all_results:
        try:
            img  = Image.open(p)
            dims = f"{img.width}x{img.height}"
        except Exception:
            dims = "???"
        status = "OK  " if ok else "FAIL"
        print(f"  [{status}] {dims:12s} {os.path.basename(p)}")

    if failed:
        print("\nDIMENSION CHECK FAILURES:")
        for p, _ in failed:
            print(f"  {p}")
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED")


def _derive_theme_label(title: str) -> str:
    """Extract a 2-3 word theme label from the article title.

    Strips common stop words and returns the most meaningful short phrase.
    Used for the Feature image THEME text layer (Aleo SemiBold).
    """
    stop = {"a", "an", "the", "is", "are", "was", "were", "to", "for", "of",
            "in", "on", "at", "by", "and", "or", "but", "you", "your", "my",
            "it", "its", "do", "does", "how", "why", "what", "when", "where",
            "will", "can", "could", "should", "would", "before", "after",
            "things", "actually", "get", "worse", "that"}
    words = [w.strip("?!.,:'\"").title() for w in title.split()]
    meaningful = [w for w in words if w.lower() not in stop and len(w) > 2]
    return " ".join(meaningful[:3]) if meaningful else title.split()[0]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AskRoss.ca Blog Image Pipeline")
    phase_group = parser.add_mutually_exclusive_group(required=True)
    phase_group.add_argument(
        "--phase1", action="store_true",
        help="Phase 1: solid-color test backgrounds, output to out/test-output/",
    )
    phase_group.add_argument(
        "--phase2", action="store_true",
        help="Phase 2: real AI-generated backgrounds, output to out/",
    )
    parser.add_argument("--article", default=None, help="Article filename (for logging)")
    parser.add_argument("--output-dir", default=None, help="Override output base directory")

    args   = parser.parse_args()
    phase  = 1 if args.phase1 else 2

    run_pipeline(phase=phase, output_base=args.output_dir)


if __name__ == "__main__":
    main()
