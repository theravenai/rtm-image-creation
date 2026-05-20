"""
Ground truth comparison module for the blog image creation pipeline.
Compares test output images against known-good ground truth samples.
"""

import os
import re
from pathlib import Path
from PIL import Image


def compare_images(test_img_path: str, gt_img_path: str) -> dict:
    """
    Compare two images and return similarity metrics.

    Returns dict with:
        dimensions_match  : bool
        mode_match        : bool
        test_dims         : (w, h)
        gt_dims           : (w, h)
        test_mode         : str
        gt_mode           : str
        test_topleft_px   : tuple (RGB)
        gt_topleft_px     : tuple (RGB)
        topleft_diff      : int   (sum of |R-R|+|G-G|+|B-B|)
        both_have_overlay : bool  (both images have non-uniform top-left region)
        notes             : list of str
    """
    notes = []

    try:
        test_img = Image.open(test_img_path).convert("RGB")
        gt_img   = Image.open(gt_img_path).convert("RGB")
    except Exception as exc:
        return {"error": str(exc), "notes": [str(exc)]}

    test_dims = test_img.size
    gt_dims   = gt_img.size
    dims_match = (test_dims == gt_dims)
    if not dims_match:
        notes.append(f"Dimension mismatch: test={test_dims} vs gt={gt_dims}")

    test_raw_mode = Image.open(test_img_path).mode
    gt_raw_mode   = Image.open(gt_img_path).mode
    mode_match    = (test_raw_mode == gt_raw_mode)
    if not mode_match:
        notes.append(f"Mode mismatch: test={test_raw_mode} vs gt={gt_raw_mode}")

    # Top-left overlay region
    test_tl = test_img.getpixel((20, 20))
    gt_tl   = gt_img.getpixel((20, 20))
    tl_diff = sum(abs(a - b) for a, b in zip(test_tl, gt_tl))

    # Check for overlay uniformity (top-left vs center)
    OVERLAY_THRESHOLD = 30
    cx = min(test_dims[0] // 2, gt_dims[0] // 2)
    cy = min(test_dims[1] // 2, gt_dims[1] // 2)

    test_center = test_img.getpixel((cx, cy))
    gt_center   = gt_img.getpixel((cx, cy))

    test_overlay_diff = sum(abs(a - b) for a, b in zip(test_tl, test_center))
    gt_overlay_diff   = sum(abs(a - b) for a, b in zip(gt_tl, gt_center))

    test_has_overlay = test_overlay_diff >= OVERLAY_THRESHOLD
    gt_has_overlay   = gt_overlay_diff   >= OVERLAY_THRESHOLD
    both_have_overlay = test_has_overlay and gt_has_overlay

    if not test_has_overlay:
        notes.append("Test image does NOT appear to have overlay in top-left corner")
    if not gt_has_overlay:
        notes.append("Ground truth image does NOT appear to have overlay in top-left corner (unexpected)")
    if both_have_overlay:
        notes.append("Both images have overlay detected in top-left corner — consistent")

    test_img.close()
    gt_img.close()

    return {
        "dimensions_match":  dims_match,
        "mode_match":        mode_match,
        "test_dims":         test_dims,
        "gt_dims":           gt_dims,
        "test_mode":         test_raw_mode,
        "gt_mode":           gt_raw_mode,
        "test_topleft_px":   test_tl,
        "gt_topleft_px":     gt_tl,
        "topleft_diff":      tl_diff,
        "test_overlay_diff": test_overlay_diff,
        "gt_overlay_diff":   gt_overlay_diff,
        "both_have_overlay": both_have_overlay,
        "notes":             notes,
    }


def _find_first_png(directory: Path, exclude_raw: bool = False) -> Path | None:
    """Return first PNG file in a directory."""
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() == ".png":
            if exclude_raw and "RAW" in f.name:
                continue
            return f
    return None


def run_comparison(test_output_dir: str, ground_truth_dir: str) -> dict:
    """
    Compare test output folder vs ground truth folder.
    Picks one representative image from each category and compares.

    Returns dict with:
        comparisons : list of per-category comparison results
        overall_ok  : bool — True if all compared images pass
        summary     : str
    """
    test_root = Path(test_output_dir)
    gt_root   = Path(ground_truth_dir)

    comparisons = []
    all_ok = True

    # 1) Feature image
    test_feature = next(
        (f for f in test_root.iterdir()
         if f.is_file() and f.name.startswith("Feature Image -")),
        None,
    )
    gt_feature = next(
        (f for f in gt_root.iterdir()
         if f.is_file() and f.name.startswith("Feature Image -")),
        None,
    )
    if test_feature and gt_feature:
        cmp = compare_images(str(test_feature), str(gt_feature))
        cmp["category"] = "Feature Image"
        cmp["test_file"] = test_feature.name
        cmp["gt_file"]   = gt_feature.name
        comparisons.append(cmp)
        if not (cmp.get("dimensions_match") and cmp.get("mode_match")):
            all_ok = False
    else:
        comparisons.append({
            "category": "Feature Image",
            "error": f"Missing file: test={test_feature}, gt={gt_feature}",
        })
        all_ok = False

    # 2) Article image (first one alphabetically)
    test_article_dir = test_root / "BLOG POST - Large Article Images for Askross.ca"
    gt_article_dir   = gt_root   / "BLOG POST - Large Article Images for Askross.ca"
    test_article = _find_first_png(test_article_dir) if test_article_dir.is_dir() else None
    gt_article   = _find_first_png(gt_article_dir)   if gt_article_dir.is_dir() else None
    if test_article and gt_article:
        cmp = compare_images(str(test_article), str(gt_article))
        cmp["category"] = "Article Image"
        cmp["test_file"] = test_article.name
        cmp["gt_file"]   = gt_article.name
        comparisons.append(cmp)
        if not cmp.get("dimensions_match"):
            all_ok = False
    else:
        comparisons.append({
            "category": "Article Image",
            "error": f"Missing: test={test_article}, gt={gt_article}",
        })
        all_ok = False

    # 3) GMB image (Toronto)
    test_gmb_dir = test_root / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE"
    gt_gmb_dir   = gt_root   / "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE"
    test_gmb = next(
        (f for f in sorted(test_gmb_dir.iterdir())
         if f.is_file() and f.name.lower().startswith("toronto")),
        None,
    ) if test_gmb_dir.is_dir() else None
    gt_gmb = next(
        (f for f in sorted(gt_gmb_dir.iterdir())
         if f.is_file() and f.name.lower().startswith("toronto")),
        None,
    ) if gt_gmb_dir.is_dir() else None
    if test_gmb and gt_gmb:
        cmp = compare_images(str(test_gmb), str(gt_gmb))
        cmp["category"] = "GMB Image (Toronto)"
        cmp["test_file"] = test_gmb.name
        cmp["gt_file"]   = gt_gmb.name
        comparisons.append(cmp)
        if not cmp.get("dimensions_match"):
            all_ok = False
    else:
        comparisons.append({
            "category": "GMB Image (Toronto)",
            "error": f"Missing: test={test_gmb}, gt={gt_gmb}",
        })
        all_ok = False

    # 4) Banner
    test_banner = next(
        (f for f in test_root.iterdir()
         if f.is_file() and f.name.startswith("Banner -")),
        None,
    )
    gt_banner = next(
        (f for f in gt_root.iterdir()
         if f.is_file() and f.name.startswith("Banner -")),
        None,
    )
    if test_banner and gt_banner:
        cmp = compare_images(str(test_banner), str(gt_banner))
        cmp["category"] = "Banner"
        cmp["test_file"] = test_banner.name
        cmp["gt_file"]   = gt_banner.name
        comparisons.append(cmp)
        if not cmp.get("dimensions_match"):
            all_ok = False
    else:
        comparisons.append({
            "category": "Banner",
            "error": f"Missing: test={test_banner}, gt={gt_banner}",
        })
        all_ok = False

    summary = "All compared images match ground truth" if all_ok else "Some images differ from ground truth"
    return {
        "comparisons": comparisons,
        "overall_ok":  all_ok,
        "summary":     summary,
    }
