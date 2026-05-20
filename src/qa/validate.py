"""
QA validation module for the blog image creation pipeline.
Validates test output against required specifications.
"""

import os
import re
from pathlib import Path
from PIL import Image


# ── Expected dimensions by image category ───────────────────────────────────
EXPECTED_DIMS = {
    "feature":  (700, 450),
    "banner":   (1286, 300),
    "mobile":   (400, 600),
    "article":  (1920, 1080),
    "gmb":      (1200, 900),
}

# ── Naming patterns ──────────────────────────────────────────────────────────
PATTERN_FEATURE  = re.compile(r"^Feature Image - .+\.png$", re.IGNORECASE)
PATTERN_FEATURE_RAW = re.compile(r"^.+ - Feature Background RAW\.png$", re.IGNORECASE)
PATTERN_BANNER   = re.compile(r"^Banner - .+\.png$", re.IGNORECASE)
PATTERN_MOBILE   = re.compile(r"^Mobile - .+\.png$", re.IGNORECASE)
PATTERN_ARTICLE  = re.compile(r"^AskRoss\.ca - .+\.png$", re.IGNORECASE)
PATTERN_GMB      = re.compile(r"^(Toronto|Ottawa|Richmond Hill|Mississauga) - .+\.png$", re.IGNORECASE)

GMB_CITIES = {"toronto", "ottawa", "richmond hill", "mississauga"}


def _open_rgb(path: str) -> Image.Image:
    img = Image.open(path).convert("RGB")
    return img


def _color_distance(px1: tuple, px2: tuple) -> int:
    """Sum of absolute channel differences between two RGB pixels."""
    return sum(abs(a - b) for a, b in zip(px1, px2))


# ── Individual checks ────────────────────────────────────────────────────────

def check_folder_structure(test_output_dir: str) -> dict:
    """Check 7: Verify the required folder structure exists."""
    name = "Check 7: Folder structure"
    root = Path(test_output_dir)

    required_files = [
        root / "Feature Image - Should You Sell Your Home Before Things Get Worse.png",
        root / "Should You Sell Your Home Before Things Get Worse - Feature Background RAW.png",
        root / "Banner - Should You Sell Your Home Before Things Get Worse.png",
        root / "Mobile - Should You Sell Your Home Before Things Get Worse.png",
    ]
    required_dirs = [
        root / "BLOG POST - Large Article Images for Askross.ca",
        root / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE",
    ]

    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(str(f.name))
    for d in required_dirs:
        if not d.is_dir():
            missing.append(str(d.name) + "/")

    if missing:
        return {"check": name, "status": "FAIL", "reason": f"Missing: {missing}"}
    return {"check": name, "status": "PASS"}


def check_file_count(test_output_dir: str) -> dict:
    """Check 2: Verify file counts in each section."""
    name = "Check 2: File count"
    root = Path(test_output_dir)

    article_dir = root / "BLOG POST - Large Article Images for Askross.ca"
    gmb_dir     = root / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE"

    failures = []
    details  = []

    # Root files (Feature Image, Feature Background RAW, Banner, Mobile)
    root_pngs = [f for f in root.iterdir() if f.is_file() and f.suffix.lower() == ".png"]
    details.append(f"Root PNG count: {len(root_pngs)} (expected 4)")
    if len(root_pngs) != 4:
        failures.append(f"Root folder has {len(root_pngs)} PNG file(s); expected 4")

    # Article images
    if article_dir.is_dir():
        article_pngs = [f for f in article_dir.iterdir() if f.is_file() and f.suffix.lower() == ".png"]
        details.append(f"Article images count: {len(article_pngs)} (expected >= 9)")
        if len(article_pngs) < 9:
            failures.append(f"Article images folder has {len(article_pngs)} file(s); expected >= 9")
    else:
        failures.append("Article images subfolder does not exist")

    # GMB images
    if gmb_dir.is_dir():
        gmb_pngs = [f for f in gmb_dir.iterdir() if f.is_file() and f.suffix.lower() == ".png"]
        details.append(f"GMB images count: {len(gmb_pngs)} (expected 4)")
        if len(gmb_pngs) != 4:
            failures.append(f"GMB images folder has {len(gmb_pngs)} file(s); expected exactly 4")
    else:
        failures.append("GMB images subfolder does not exist")

    if failures:
        return {"check": name, "status": "FAIL", "reason": "; ".join(failures), "details": details}
    return {"check": name, "status": "PASS", "details": details}


def check_dimensions(test_output_dir: str) -> dict:
    """Check 1: Verify pixel dimensions for every output image."""
    name = "Check 1: Dimensions"
    root = Path(test_output_dir)
    failures = []
    checked  = []

    def _verify(path: Path, expected_wh: tuple):
        img = _open_rgb(str(path))
        actual = img.size  # (width, height)
        img.close()
        ok = (actual == expected_wh)
        checked.append(f"{path.name}: {actual[0]}x{actual[1]} (expected {expected_wh[0]}x{expected_wh[1]}) {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{path.name}: got {actual[0]}x{actual[1]}, expected {expected_wh[0]}x{expected_wh[1]}")

    # Root files
    for f in root.iterdir():
        if not (f.is_file() and f.suffix.lower() == ".png"):
            continue
        n = f.name
        if PATTERN_FEATURE_RAW.match(n):
            _verify(f, EXPECTED_DIMS["feature"])  # RAW file same canvas as feature
        elif PATTERN_FEATURE.match(n):
            _verify(f, EXPECTED_DIMS["feature"])
        elif PATTERN_BANNER.match(n):
            _verify(f, EXPECTED_DIMS["banner"])
        elif PATTERN_MOBILE.match(n):
            _verify(f, EXPECTED_DIMS["mobile"])

    # Article images
    article_dir = root / "BLOG POST - Large Article Images for Askross.ca"
    if article_dir.is_dir():
        for f in article_dir.iterdir():
            if f.is_file() and f.suffix.lower() == ".png":
                _verify(f, EXPECTED_DIMS["article"])

    # GMB images
    gmb_dir = root / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE"
    if gmb_dir.is_dir():
        for f in gmb_dir.iterdir():
            if f.is_file() and f.suffix.lower() == ".png":
                _verify(f, EXPECTED_DIMS["gmb"])

    if failures:
        return {"check": name, "status": "FAIL", "reason": "; ".join(failures), "details": checked}
    return {"check": name, "status": "PASS", "details": checked}


def check_naming_convention(test_output_dir: str) -> dict:
    """Check 3: Verify naming conventions."""
    name = "Check 3: Naming convention"
    root = Path(test_output_dir)
    failures = []

    # Root files
    for f in root.iterdir():
        if not (f.is_file() and f.suffix.lower() == ".png"):
            continue
        n = f.name
        matched = (
            PATTERN_FEATURE.match(n)
            or PATTERN_FEATURE_RAW.match(n)
            or PATTERN_BANNER.match(n)
            or PATTERN_MOBILE.match(n)
        )
        if not matched:
            failures.append(f"Root file does not match any expected pattern: {n}")

    # Article images
    article_dir = root / "BLOG POST - Large Article Images for Askross.ca"
    if article_dir.is_dir():
        for f in article_dir.iterdir():
            if f.is_file() and f.suffix.lower() == ".png":
                if not PATTERN_ARTICLE.match(f.name):
                    failures.append(f"Article image bad name: {f.name}")

    # GMB images
    gmb_dir = root / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE"
    if gmb_dir.is_dir():
        for f in gmb_dir.iterdir():
            if f.is_file() and f.suffix.lower() == ".png":
                if not PATTERN_GMB.match(f.name):
                    failures.append(f"GMB image bad name (must start with city): {f.name}")

    if failures:
        return {"check": name, "status": "FAIL", "reason": "; ".join(failures)}
    return {"check": name, "status": "PASS"}


def check_overlay_presence(test_output_dir: str) -> dict:
    """
    Check 4: Verify overlay IS applied on article and GMB images.

    Detection strategy: the overlay PNG is a uniform semi-transparent dark scrim
    (alpha=74 everywhere, RGBA 0,0,0,74) plus a logo region with higher alpha in the
    top-left corner.  When composited on the solid Phase-1 test backgrounds the result
    is a uniformly darker image — NOT a contrast difference between top-left and center.

    Correct detection approach:
      - Phase 1 article background color: (100, 100, 110)
      - Phase 1 feature/banner/GMB background color: (80, 80, 90) or similar
      - After overlay compositing the image is DARKER than the raw background
      - We verify overlay is present by checking that pixels are NOT equal to the
        raw background colors (raw bg would be ~(80-110, 80-110, 90-110); with overlay
        they drop to ~(50-75, 50-75, 55-80))
      - Additionally, white pixels (R>200) must exist for the logo (always present)

    For Phase 2 (real photo backgrounds): if the image has significant pixel variation
    (R_range > 30 across a sample), we confirm overlay via logo white pixels in the
    top-left band (y=20-90, x=20-230).
    """
    name = "Check 4: Overlay presence"
    root = Path(test_output_dir)
    failures = []
    warnings = []
    details  = []

    # Phase 1 raw background colors (before any overlay)
    PHASE1_ARTICLE_BG = (100, 100, 110)
    PHASE1_FEATURE_BG = (80, 80, 90)

    def _sample_pixels(img: Image.Image, step: int = 100) -> list:
        """Return a flat list of RGB pixel tuples sampled across the image."""
        return [img.getpixel((x, y))
                for y in range(0, img.height, step)
                for x in range(0, img.width, step)]

    def _r_range(pixels: list) -> int:
        """Red channel range across sampled pixels."""
        rs = [p[0] for p in pixels]
        return max(rs) - min(rs)

    def _has_logo_white_pixels(img: Image.Image, logo_region: tuple) -> bool:
        """
        Check for white/light pixels in the logo region.

        logo_region: (x_start, y_start, x_end, y_end)
          - Article images: logo is top-left (x=20-230, y=20-90)
          - GMB images:     logo is mid-left (x=236-422, y=456-686)
        """
        x0, y0, x1, y1 = logo_region
        for y in range(y0, y1, 3):
            for x in range(x0, x1, 3):
                if x < img.width and y < img.height:
                    px = img.getpixel((x, y))
                    # Logo pixels in the GMB template tend to be grey/white against dark bg
                    if px[0] > 150 and px[1] > 150 and px[2] > 150:
                        return True
        return False

    # Article logo region: top-left, Y=20-90, X=20-230
    ARTICLE_LOGO_REGION = (20, 20, 230, 90)
    # GMB logo region: mid-left, Y=456-686, X=236-422
    GMB_LOGO_REGION     = (236, 456, 422, 686)

    def _check_overlay(path: Path, phase1_raw_bg: tuple, logo_region: tuple) -> tuple:
        """
        Returns (has_overlay: bool, detail_str: str).

        Strategy:
        1. If the image has high pixel variance (real photo bg), check for logo
           light pixels in the image-specific logo region.
        2. If the image is near-uniform (solid-color Phase-1 bg), verify pixels are
           DIFFERENT from the raw background color — indicating overlay darkened them.
           Additionally check for logo pixels.
        """
        img = _open_rgb(str(path))
        pixels = _sample_pixels(img, step=100)
        r_rng  = _r_range(pixels)
        sample_px = pixels[0]

        if r_rng > 30:
            # Real photo background — check for logo light pixels in logo region
            has_logo = _has_logo_white_pixels(img, logo_region)
            img.close()
            detail = (f"pixel_variance=high (R_range={r_rng}), logo_pixels={'YES' if has_logo else 'NO'} "
                      f"-> {'OVERLAY OK' if has_logo else 'NO OVERLAY'}")
            return has_logo, detail
        else:
            # Solid/near-uniform background
            # Check if pixels differ from the raw Phase-1 background color
            dist_from_raw = _color_distance(sample_px, phase1_raw_bg)
            has_logo      = _has_logo_white_pixels(img, logo_region)
            img.close()
            # Overlay is present if pixels are meaningfully different from raw bg
            # OR if logo pixels exist
            overlay_detected = (dist_from_raw >= 5) or has_logo
            detail = (f"sample_px={sample_px}, raw_bg={phase1_raw_bg}, "
                      f"dist_from_raw={dist_from_raw}, logo_pixels={'YES' if has_logo else 'NO'} "
                      f"-> {'OVERLAY OK' if overlay_detected else 'NO OVERLAY'}")
            return overlay_detected, detail

    # Article images — overlay MUST be present
    article_dir = root / "BLOG POST - Large Article Images for Askross.ca"
    if article_dir.is_dir():
        for f in sorted(article_dir.iterdir()):
            if not (f.is_file() and f.suffix.lower() == ".png"):
                continue
            has_ov, detail = _check_overlay(f, PHASE1_ARTICLE_BG, ARTICLE_LOGO_REGION)
            details.append(f"  Article {f.name}: {detail}")
            if not has_ov:
                failures.append(f"No overlay detected in article image: {f.name}")

    # GMB images — overlay MUST be present
    gmb_dir = root / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE"
    if gmb_dir.is_dir():
        for f in sorted(gmb_dir.iterdir()):
            if not (f.is_file() and f.suffix.lower() == ".png"):
                continue
            has_ov, detail = _check_overlay(f, PHASE1_FEATURE_BG, GMB_LOGO_REGION)
            details.append(f"  GMB {f.name}: {detail}")
            if not has_ov:
                failures.append(f"No overlay detected in GMB image: {f.name}")

    # Feature Background RAW — overlay must NOT be applied (should be uniform)
    raw_files = [f for f in root.iterdir() if PATTERN_FEATURE_RAW.match(f.name)]
    if raw_files:
        raw = raw_files[0]
        img = _open_rgb(str(raw))
        pixels = _sample_pixels(img, step=50)
        r_rng  = _r_range(pixels)
        sample_px = pixels[0]
        img.close()
        details.append(f"  RAW file {raw.name}: sample_px={sample_px}, R_range={r_rng}")
        if r_rng > 30:
            warnings.append(
                f"Feature Background RAW has high pixel variance (R_range={r_rng}). "
                "If this is Phase 1 (solid bg), overlay may have been applied unexpectedly."
            )
        else:
            details[-1] += " -> uniform background (expected for RAW)"
    else:
        warnings.append("Feature Background RAW file not found — cannot verify no-overlay condition")

    if failures:
        return {"check": name, "status": "FAIL", "reason": "; ".join(failures),
                "details": details, "warnings": warnings}
    return {"check": name, "status": "PASS", "details": details, "warnings": warnings}


def check_text_presence(test_output_dir: str) -> dict:
    """
    Check 5: For article images (non-bottom-line, non-faq), verify white pixels
    exist in the text zone.

    Auto-text-position places text at one of three positions in 1920x1080 images:
      - upper-left:  y ~ 200-310
      - lower-left:  y ~ 840-960
      - center:      y ~ 480-600
    We scan the ENTIRE image (excluding the logo band y=0-100) for white pixel clusters
    outside the known logo area, confirming text was rendered.
    Logo region: y=20-85, x=20-230 (white logo pixels do not count as text).
    """
    name = "Check 5: Text presence"
    root = Path(test_output_dir)
    article_dir = root / "BLOG POST - Large Article Images for Askross.ca"
    failures = []
    details  = []

    if not article_dir.is_dir():
        return {"check": name, "status": "FAIL", "reason": "Article images subfolder not found"}

    for f in sorted(article_dir.iterdir()):
        if not (f.is_file() and f.suffix.lower() == ".png"):
            continue

        fn_lower = f.name.lower()
        is_bottom_line = "bottom line" in fn_lower
        is_faq         = "faq" in fn_lower

        if is_bottom_line:
            details.append(f"  {f.name}: bottom-line — text check skipped (reusable layout, no text step)")
            continue

        img = _open_rgb(str(f))
        w, h = img.size

        if is_faq:
            # FAQ images DO have text rendered — scan full image
            pass

        # Scan the full image for white pixels, excluding the logo band (y=0-100, x=0-240)
        # Sample every 5px for accuracy (not every 10px — text is thin at 48px)
        white_outside_logo = 0
        for y in range(100, h, 5):  # skip logo y-band
            for x in range(0, w, 5):
                px = img.getpixel((x, y))
                if px[0] > 200 and px[1] > 200 and px[2] > 200:
                    white_outside_logo += 1
        img.close()

        has_text = white_outside_logo > 0
        details.append(
            f"  {f.name}: white_px_outside_logo={white_outside_logo} "
            f"-> {'TEXT OK' if has_text else 'NO TEXT'}"
        )
        if not has_text:
            failures.append(f"No text (white pixels outside logo area) found in: {f.name}")

    if failures:
        return {"check": name, "status": "FAIL", "reason": "; ".join(failures), "details": details}
    return {"check": name, "status": "PASS", "details": details}


def check_rgb_mode(test_output_dir: str) -> dict:
    """Check 6 (partial): Verify all final output images are RGB (not RGBA)."""
    name = "Check 6: RGB mode (no alpha)"
    root = Path(test_output_dir)
    failures = []
    details  = []

    all_pngs = list(root.rglob("*.png"))
    # Exclude the RAW background — it could technically be RGB or RGBA
    for f in all_pngs:
        img = Image.open(str(f))
        mode = img.mode
        img.close()
        ok = (mode == "RGB")
        details.append(f"  {f.name}: mode={mode} -> {'OK' if ok else 'FAIL (has alpha)'}")
        if not ok:
            failures.append(f"{f.name}: mode={mode}, expected RGB")

    if failures:
        return {"check": name, "status": "FAIL", "reason": "; ".join(failures), "details": details}
    return {"check": name, "status": "PASS", "details": details}


# ── Main runner ──────────────────────────────────────────────────────────────

def run_all_checks(test_output_dir: str, ground_truth_dir: str) -> dict:
    """
    Run all QA checks against the test output.

    Returns:
        {
            "passed":   list of check names that passed,
            "failed":   list of {"check": name, "reason": detail, "details": [...optional]},
            "warnings": list of non-fatal issues,
            "details":  dict mapping check name -> detail lines
        }
    """
    results  = {
        "passed":   [],
        "failed":   [],
        "warnings": [],
        "details":  {},
    }

    checks = [
        check_folder_structure,
        check_file_count,
        check_dimensions,
        check_naming_convention,
        check_overlay_presence,
        check_text_presence,
        check_rgb_mode,
    ]

    for check_fn in checks:
        try:
            result = check_fn(test_output_dir)
        except Exception as exc:
            result = {
                "check":  check_fn.__name__,
                "status": "FAIL",
                "reason": f"Exception during check: {exc}",
            }

        check_name = result["check"]
        status     = result.get("status", "FAIL")
        reason     = result.get("reason", "")
        detail_lines = result.get("details", [])
        warn_lines   = result.get("warnings", [])

        results["details"][check_name] = detail_lines

        if warn_lines:
            for w in warn_lines:
                results["warnings"].append(f"[{check_name}] {w}")

        if status == "PASS":
            results["passed"].append(check_name)
        else:
            results["failed"].append({"check": check_name, "reason": reason})

    return results
