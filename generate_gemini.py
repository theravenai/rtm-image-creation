"""
generate_gemini.py — Generate blog image backgrounds via Gemini 2.5 Flash Image (OpenRouter).

Reads out/manifest.json, generates one background image per H2 section (using the
prompt_hint field) plus the shared feature/banner/GMB background, then runs the full
compositing pipeline.

Output:
  out/generated/gemini_feature_bg.png            — shared background for feature/banner/GMB
  out/generated/gemini_{filename_base}.png        — per-section article backgrounds
  out/Blog Images - Gemini - {title}/             — final composited images

Usage:
  python generate_gemini.py

Requires:
  OPENROUTER_IMAGE_API_KEY in .env
"""

import base64
import datetime
import glob as glob_mod
import io
import json
import os
import random
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

SCRIPT_DIR    = Path(__file__).parent.resolve()
REF_DIR       = SCRIPT_DIR / "references"
GENERATED_DIR = SCRIPT_DIR / "out" / "generated"

_DEFAULT_MODEL = "google/gemini-2.5-flash-image"

_HOME_FOR_SALE_POOL = str(
    REF_DIR / "BLOG POST - Large Article Images for Askross.ca"
    / "Reusable Image Large Article Image Assets" / "home for sale options" / "*.png"
)


def _get_model() -> str:
    return os.environ.get("OPENROUTER_IMAGE_MODEL", _DEFAULT_MODEL)


def _load_env():
    local    = SCRIPT_DIR / ".env"
    fallback = REF_DIR / "(2) Newsletter Image Creation - Use for process creation reference" / ".env"
    if local.exists():
        load_dotenv(local)
    elif fallback.exists():
        load_dotenv(fallback)


def _is_selling_article(title: str) -> bool:
    low = title.lower()
    return any(kw in low for kw in ("sell", "selling", "for sale"))


def _current_season() -> str:
    month = datetime.date.today().month
    if month in (3, 4, 5):   return "spring"
    if month in (6, 7, 8):   return "summer"
    if month in (9, 10, 11): return "autumn"
    return "winter"


def _style_suffix() -> str:
    """Return the standard photographic constraints suffix for all prompts.

    Incorporates prompt-builder.md rules: rule of thirds, upper-left quiet zone,
    seasonal accuracy, no-face-forward, no AI tells, Canadian context only.
    """
    season = _current_season()
    return (
        f" Photorealistic editorial photography, 16:9 wide aspect ratio. "
        f"Rule of thirds: focal subject's eyeline (people) or center of mass (objects) on the upper-third horizontal line. "
        f"Upper-left corner (~260x100px) must be visually quiet — clear sky, blurred foliage, or plain wall — for logo overlay. "
        f"Subject sized to occupy 35–55 percent of the frame's vertical height. "
        f"Current season is {season} in Canada — use appropriate foliage (no autumn/fall colours unless season is autumn). "
        f"No readable text, logos, watermarks, or legible signage in the image. "
        f"Avoiding: cropped heads or chins at frame edge, subject too small in frame, excessive sky over 30 percent of frame, "
        f"person staring directly head-on into the camera lens, business handshakes, thumbs-up gestures, "
        f"diverse team pointing at chart, coins stacked in glass jars, rubber stamps, "
        f"American flags, palm trees, Spanish-tile roofs, US architectural markers, "
        f"plastic-textured skin, distorted hands, fused fingers, AI generation artifacts, illustration look, 3D render style, "
        f"heavy Instagram filters, surreal or fantasy elements."
    )


# ---------------------------------------------------------------------------
# Gemini image generation
# ---------------------------------------------------------------------------

_FALLBACK_PROMPTS = [
    "A bright, welcoming Canadian suburban home exterior on a clear spring morning, wide angle, editorial photography, no people, upper-left sky kept clear.",
    "A clean Canadian kitchen counter with documents and a coffee mug, soft window light, documentary still-life, no people.",
    "A well-maintained Canadian residential street, spring foliage, blue sky, wide landscape, no people.",
]


def _generate_image(prompt: str, api_key: str, label: str) -> Image.Image | None:
    """Generate a single image via OpenRouter Gemini Flash Image.

    Returns PIL Image, or None if the model refuses after all retries.
    Tries the original prompt first, then progressively simpler fallback prompts.
    """
    model = _get_model()
    prompts_to_try = [prompt] + _FALLBACK_PROMPTS

    for attempt, p in enumerate(prompts_to_try):
        if attempt == 0:
            print(f"  Generating: {label}")
            print(f"    Prompt: {p[:80]}{'...' if len(p) > 80 else ''}")
        else:
            print(f"    Retry {attempt} with fallback prompt...")

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": p}],
            },
            timeout=180,
        )
        r.raise_for_status()
        data = r.json()

        try:
            img_url = data["choices"][0]["message"]["images"][0]["image_url"]["url"]
            b64 = img_url.split(",", 1)[1]
            img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
            print(f"    Got: {img.width}x{img.height}")
            return img
        except (KeyError, IndexError, TypeError):
            print(f"    Model returned no image (filtered). {'Trying fallback.' if attempt < len(prompts_to_try) - 1 else 'Giving up.'}")
            time.sleep(1)

    return None


# ---------------------------------------------------------------------------
# Prompt builders  (framework: references/(2) Newsletter.../prompt-builder.md)
# ---------------------------------------------------------------------------

def _prompt_for_feature(title: str, theme_label: str) -> str:
    """Return None for selling articles (use home for sale pool instead)."""
    low = title.lower()
    if "sell" in low or "selling" in low or "for sale" in low:
        return None  # caller will use home for sale pool
    if "bank of canada" in low or "rate" in low:
        return (
            "PLACE mode. The neoclassical limestone facade of the Bank of Canada building in Ottawa "
            "filling the lower two-thirds of the frame, Canadian flag mid-pole on the left edge, "
            "building centre of mass aligned to the upper-third horizontal line, "
            "soft overcast morning sky filling only the top 25 percent of the frame, "
            "wide architectural perspective, grounded and observational mood."
            + _style_suffix()
        )
    if "renewal" in low or "payment shock" in low:
        return (
            "OBJECT mode. A mortgage renewal letter and an open calendar resting on a kitchen counter, "
            "pen beside it, a coffee mug in soft focus background, soft warm overhead kitchen light, "
            "the renewal letter occupying 40 percent of the frame with its centre on the upper-third line, "
            "cautionary documentary still-life mood."
            + _style_suffix()
        )
    if "equity" in low or "underwater" in low:
        return (
            "OBJECT mode. A ceramic miniature house model sinking into a mound of sand, "
            "an empty piggy bank tipped on its side beside it, neutral studio background, "
            "objects centred on the upper-third horizontal line occupying 45 percent of vertical frame height, "
            "muted grey tones, financial loss concept, shallow depth of field."
            + _style_suffix()
        )
    return (
        "PLACE mode. A well-maintained Canadian residential street lined with maple trees in full spring-green leaf, "
        "Victorian semi-detached homes visible, late-morning soft light, "
        "street and homes filling the lower two-thirds of the frame with sky limited to the top 25 percent, "
        "real estate editorial feel, calm and informative mood."
        + _style_suffix()
    )


def _prompt_for_section(section: dict) -> str:
    """Build a prompt using prompt-builder.md framework: choose scene mode, match mood."""
    text = section.get("text", "").lower()
    suffix = _style_suffix()

    # Section 1 — what is actually happening to Canadian homeowners right now
    if "actually happening" in text or "right now" in text:
        return (
            "PEOPLE mode. A Canadian couple in their mid-thirties seated at a kitchen table, "
            "looking together at documents and a laptop screen, looking at the documents NOT at the camera, "
            "natural worried-but-engaged body language, both heads fully in frame with eyelines on the upper-third line, "
            "shoulders and upper torso visible, spring morning light through a nearby window, "
            "contemporary Canadian suburban kitchen, quiet cautionary mood."
            + suffix
        )

    # Section 2 — mortgage renewals
    if "renewal" in text or "mortgage" in text and "worse" in text:
        return (
            "OBJECT mode. A mortgage renewal letter on a kitchen counter with a calendar open behind it "
            "showing a circled upcoming date, a pen laid beside the letter, a coffee mug in soft focus background, "
            "the renewal letter's centre of mass on the upper-third horizontal line, "
            "occupying 40 percent of the frame's vertical height, soft warm kitchen light, "
            "documentary still-life, cautionary mood."
            + suffix
        )

    # Section 3 — equity disappears
    if "equity" in text or "underwater" in text:
        return (
            "OBJECT mode. A ceramic miniature house model sinking into a mound of fine sand, "
            "an empty cracked piggy bank tipped on its side beside it, neutral light grey studio background, "
            "objects centred on the upper-third horizontal line occupying 45 percent of frame height, "
            "muted grey and beige tones, shallow depth of field, financial loss concept."
            + suffix
        )

    # Section 4 — warning signs / forced sale
    if "warning" in text or "forced sale" in text:
        return (
            "PLACE mode. A Canadian suburban home exterior with several bright red flag markers staked visibly "
            "in the front yard, overcast spring sky, the house facade filling the lower two-thirds of the frame, "
            "roofline sitting on the upper-third horizontal line, red flags clearly visible as the visual story element, "
            "no people in the frame, the flags and house speak for themselves, ominous cautionary mood."
            + suffix
        )

    # Section 5 — waiting for market to recover
    if "waiting" in text or "market" in text and "recover" in text:
        return (
            "OBJECT mode. A glass hourglass with sand flowing, resting on an open monthly calendar, "
            "the hourglass centred on the upper-third horizontal line occupying 40 percent of frame height, "
            "neutral dark desk surface, soft directional side light, muted contemplative mood, "
            "no people, no clutter."
            + suffix
        )

    # Section 6 — selling affects credit
    if "credit" in text or "selling" in text and "affect" in text:
        return (
            "OBJECT mode. A laptop screen showing a credit score gauge moving from the red zone to green, "
            "the laptop centred on the upper-third horizontal line occupying 45 percent of frame height, "
            "clean desk surface, soft ambient light, no person visible, "
            "optimistic resolution mood, simple and uncluttered composition."
            + suffix
        )

    # Section 7 — financial reset
    if "reset" in text or "fresh start" in text or "financial reset" in text:
        return (
            "PEOPLE mode. A Canadian couple in their thirties seated at a bright kitchen table, "
            "looking together at a tablet screen showing a budget or financial plan, "
            "looking at the tablet NOT at the camera, warm optimistic body language, "
            "both heads fully in frame with eyelines on the upper-third line, "
            "spring morning light through a large window behind them, fresh-start optimistic mood."
            + suffix
        )

    # Generic fallback
    hint = section.get("prompt_hint", "").strip()
    if hint:
        return hint + suffix
    return (
        "PLACE mode. A well-maintained Canadian suburban home on a quiet residential street, "
        "spring foliage, editorial real estate photography."
        + suffix
    )


def _prompt_for_bottom_line(manifest: dict) -> str:
    """Contextually relevant background for the Advice/Bottom Line image."""
    title = manifest.get("title", "").lower()
    suffix = _style_suffix()
    if "sell" in title or "selling" in title or "for sale" in title:
        return (
            "PEOPLE mode. A Canadian couple in their forties standing on the front porch steps of their "
            "suburban home on a bright spring morning, looking at each other in quiet thoughtful conversation, "
            "calm and considered decision-making body language — NOT looking at the camera, "
            "both heads fully in frame with eyelines on the upper-third line, "
            "green spring foliage, Canadian residential home facade fills the background, "
            "warm morning light, resolved and hopeful mood."
            + suffix
        )
    if "renewal" in title or "rate" in title:
        return (
            "PEOPLE mode. A Canadian couple seated across from a professional mortgage advisor at a clean office desk, "
            "advisor pointing at documents, couple looking at the paperwork not the camera, "
            "warm professional lighting, reassuring and informative mood."
            + suffix
        )
    return (
        "PEOPLE mode. A professional Canadian mortgage advisor at a modern office desk, "
        "looking down at an open notepad, warm approachable lighting, "
        "advisor NOT looking at the camera, calm professional mood."
        + suffix
    )


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------

def _save(img: Image.Image, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path, "PNG")
    print(f"  Saved: {os.path.basename(path)} ({img.width}x{img.height})")


# ---------------------------------------------------------------------------
# Main Gemini workflow
# ---------------------------------------------------------------------------

def run_gemini():
    _load_env()

    print("\n=== Gemini Background Generation (OpenRouter) ===")

    api_key = os.environ.get("OPENROUTER_IMAGE_API_KEY", "")
    if not api_key:
        raise EnvironmentError("OPENROUTER_IMAGE_API_KEY not set in .env")
    print(f"  API key loaded (length={len(api_key)})")

    # Load manifest
    manifest_path = SCRIPT_DIR / "out" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"  Manifest: '{manifest['title']}' ({len(manifest['h2_sections'])} sections)")

    os.makedirs(GENERATED_DIR, exist_ok=True)

    # -----------------------------------------------------------------------
    # 1. Feature / Banner / GMB shared background
    # -----------------------------------------------------------------------
    print("\n[1] Feature / Banner / GMB background")
    theme_label   = manifest.get("theme_label", "Housing News")
    feature_prompt = _prompt_for_feature(manifest["title"], theme_label)
    feature_bg_path = str(GENERATED_DIR / "gemini_feature_bg.png")

    if _is_selling_article(manifest["title"]) or feature_prompt is None:
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
        feature_bg = _generate_image(feature_prompt, api_key, "feature background")
        if feature_bg is None:
            raise RuntimeError("Could not generate feature background — all prompts filtered.")
        _save(feature_bg, feature_bg_path)
        time.sleep(2)

    # -----------------------------------------------------------------------
    # 2. Per-H2 section backgrounds
    # -----------------------------------------------------------------------
    print("\n[2] Article section backgrounds")

    article_bgs = {}  # section_number -> PIL Image

    for section in manifest["h2_sections"]:
        sec_num = section["section_number"]
        text    = section.get("text", "")
        fname   = section["filename"].replace(".png", "")
        out_path = str(GENERATED_DIR / f"gemini_{fname}.png")

        if section["is_bottom_line"]:
            # Generate contextual bottom-line background (not random pool)
            if Path(out_path).exists():
                print(f"  Section {sec_num} (bottom-line): reusing cached")
                article_bgs[sec_num] = Image.open(out_path).convert("RGB")
            else:
                prompt = _prompt_for_bottom_line(manifest)
                img = _generate_image(prompt, api_key, f"section {sec_num} bottom-line")
                if img is not None:
                    _save(img, out_path)
                    article_bgs[sec_num] = img
                else:
                    print(f"  Section {sec_num} (bottom-line): filtered — using feature_bg fallback")
                time.sleep(2)
        elif section["is_faq"]:
            # FAQ always uses the reusable pool images — never generate with Gemini
            print(f"  Section {sec_num} (FAQ): using pool image (no generation)")
        else:
            if Path(out_path).exists():
                print(f"  Section {sec_num}: reusing cached {os.path.basename(out_path)}")
                article_bgs[sec_num] = Image.open(out_path).convert("RGB")
            else:
                prompt = _prompt_for_section(section)
                img = _generate_image(prompt, api_key, f"section {sec_num}: {text[:50]}")
                if img is None:
                    print(f"  Section {sec_num}: all prompts filtered — using feature background as fallback")
                    # article_bgs[sec_num] left unset; _composite_gemini falls back to feature_bg
                else:
                    _save(img, out_path)
                    article_bgs[sec_num] = img
                time.sleep(2)

    # -----------------------------------------------------------------------
    # 3. Composite all images
    # -----------------------------------------------------------------------
    print("\n[3] Running compositing pipeline...")
    _composite_gemini(manifest, feature_bg, article_bgs)

    print("\n=== Gemini generation complete ===")


def _composite_gemini(manifest: dict, feature_bg: Image.Image, article_bgs: dict):
    """Run full compositing pipeline with Gemini-generated backgrounds."""
    import glob as glob_mod
    import random

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
    font_opensans_bold    = str(SCRIPT_DIR / "fonts" / "Open_Sans" / "static" / "OpenSans-Bold.ttf")

    article_title = manifest["title"]
    safe_title    = sanitize_filename(article_title)
    theme_label   = _derive_theme_label(manifest)

    # Use "AI" in the folder name to distinguish from Pexels output
    gemini_title = f"AI Generated - {article_title}"
    dirs               = create_output_folder_structure(str(SCRIPT_DIR / "out"), gemini_title)
    root_dir           = dirs["root"]
    article_images_dir = dirs["article_images"]
    gmb_dir            = dirs["gmb"]

    # Article images
    print("\n  Article images...")
    for section in manifest["h2_sections"]:
        text     = section["text"]
        filename = section["filename"]
        sec_num  = section["section_number"]
        out_path = os.path.join(article_images_dir, filename)

        if section["is_bottom_line"]:
            # Use generated background instead of pool
            bg = article_bgs.get(sec_num)
            if bg is not None:
                from src.compositors.shared import resize_and_center_crop, apply_overlay, save_rgb, verify_dimensions
                canvas = resize_and_center_crop(bg, 1920, 1080)
                canvas = apply_overlay(canvas, bottom_line_overlay)
                save_rgb(canvas, out_path)
                verify_dimensions(out_path, 1920, 1080)
                print(f"\n  Bottom-line (generated bg): {os.path.basename(out_path)}")
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
    run_gemini()
