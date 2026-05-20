# QA Report — Phase 1

**Date:** 2026-05-19
**Test output:** `out/test-output/Blog Images - Should You Sell Your Home Before Things Get Worse/`
**Ground truth:** `(1) Complete Blog Article Images Sample/`
**QA scripts:** `src/qa/validate.py`, `src/qa/compare_ground_truth.py`

---

## Summary

- **Checks passed: 7/7**
- **Files validated: 17** (4 root + 9 article + 4 GMB)
- **Warnings: 0**
- **Failures: 0**

---

## Check Results

### Check 1: Dimensions — PASS

All 17 output images have exact correct pixel dimensions.

| File | Expected | Actual |
|------|----------|--------|
| Feature Image - Should You Sell Your Home Before Things Get Worse.png | 700x450 | 700x450 OK |
| Should You Sell Your Home Before Things Get Worse - Feature Background RAW.png | 700x450 | 700x450 OK |
| Banner - Should You Sell Your Home Before Things Get Worse.png | 1286x300 | 1286x300 OK |
| Mobile - Should You Sell Your Home Before Things Get Worse.png | 400x600 | 400x600 OK |
| AskRoss.ca - What is actually happening to Canadian homeowners right now.png | 1920x1080 | 1920x1080 OK |
| AskRoss.ca - How are mortgage renewals making this worse.png | 1920x1080 | 1920x1080 OK |
| AskRoss.ca - What happens when your equity disappears.png | 1920x1080 | 1920x1080 OK |
| AskRoss.ca - What are the warning signs that you're heading toward a forced sale.png | 1920x1080 | 1920x1080 OK |
| AskRoss.ca - Why is waiting for the market to recover a risky strategy.png | 1920x1080 | 1920x1080 OK |
| AskRoss.ca - How does selling your home actually affect your credit.png | 1920x1080 | 1920x1080 OK |
| AskRoss.ca - What does a financial reset actually look like.png | 1920x1080 | 1920x1080 OK |
| AskRoss.ca - Advice from Ross Taylor Mortgages_ Knowing when it's time to sell your home.png | 1920x1080 | 1920x1080 OK |
| AskRoss.ca - List of all FAQs_ Canadian homeowners who can't afford their renewal or refinance.png | 1920x1080 | 1920x1080 OK |
| Toronto - Should You Sell Your Home Before Things Get Worse.png | 1200x900 | 1200x900 OK |
| Ottawa - Should You Sell Your Home Before Things Get Worse.png | 1200x900 | 1200x900 OK |
| Richmond Hill - Should You Sell Your Home Before Things Get Worse.png | 1200x900 | 1200x900 OK |
| Mississauga - Should You Sell Your Home Before Things Get Worse.png | 1200x900 | 1200x900 OK |

---

### Check 2: File count — PASS

| Location | Expected | Actual |
|----------|----------|--------|
| Root PNG files | 4 | 4 |
| Article images subfolder | >= 9 | 9 |
| GMB images subfolder | exactly 4 | 4 |

Article images: 7 regular H2 sections + 1 bottom-line (Advice from Ross Taylor Mortgages) + 1 FAQ = 9 total.

---

### Check 3: Naming convention — PASS

All files match required naming patterns:

- Root: `Feature Image - *.png`, `* - Feature Background RAW.png`, `Banner - *.png`, `Mobile - *.png`
- Article images: all begin with `AskRoss.ca - ` (9/9)
- GMB images: all begin with one of the four city names (Toronto, Ottawa, Richmond Hill, Mississauga) followed by ` - {title}.png` (4/4)

---

### Check 4: Overlay presence — PASS

Detection method accounts for two overlay types used in this pipeline:

**Article overlay** (`(1) AskRoss.ca - Just logo and grey overlay.png`): uniform semi-transparent dark scrim (RGBA 0,0,0,74) over the full 1920x1080 canvas. Logo pixels (higher alpha) are located at Y=20–90, X=20–230 (top-left). On Phase 1 solid backgrounds the scrim darkens `(100,100,110)` to `(71,71,78)` uniformly — top-left vs center pixel difference is 0, which is expected behavior, not a failure. Detection verified by: (a) pixel value differs from raw Phase 1 background by 90 units (dist_from_raw=90), and (b) white logo pixels present in top-left band.

**GMB overlay** (`Toronto - Title.png` etc.): uniform scrim (RGBA 0,0,0,82) with GMB logo at Y=456–686, X=236–422 (mid-left). Detection verified by light pixels found in this mid-left logo region.

| Image | Method | Logo pixels | Result |
|-------|--------|-------------|--------|
| 7 regular article images (solid bg) | dist_from_raw=90, logo in top-left | YES | OVERLAY OK |
| Advice from Ross Taylor Mortgages (reusable) | high variance bg, logo in top-left | YES | OVERLAY OK |
| List of all FAQs (reusable) | high variance bg, logo in top-left | YES | OVERLAY OK |
| 4 GMB images | high variance + logo in mid-left | YES | OVERLAY OK |
| Feature Background RAW | R_range=0 | N/A | Uniform (expected — no overlay) |

---

### Check 5: Text presence — PASS

White text (Archivo Black, 48px, white) was verified present in all article images that require text rendering.

The auto-text-position algorithm selected "upper-left" for all solid-background article images in Phase 1 (because all luminance regions are equal on a flat background, so it consistently picks the lowest-luminance winner which tends to be upper-left). Text appears at approximately Y=200–310.

Detection method: scanned entire image below the logo band (Y=100 to end), every 5px, for pixels with R>200, G>200, B>200.

| Image | White pixels (outside logo) | Result |
|-------|----------------------------|--------|
| AskRoss.ca - Advice from Ross Taylor Mortgages_ Knowing when... | 4367 | TEXT OK |
| AskRoss.ca - How are mortgage renewals making this worse.png | 779 | TEXT OK |
| AskRoss.ca - How does selling your home actually affect your credit.png | 886 | TEXT OK |
| AskRoss.ca - List of all FAQs_... (FAQ image) | 1267 | TEXT OK |
| AskRoss.ca - What are the warning signs... | 1116 | TEXT OK |
| AskRoss.ca - What does a financial reset actually look like.png | 738 | TEXT OK |
| AskRoss.ca - What happens when your equity disappears.png | 742 | TEXT OK |
| AskRoss.ca - What is actually happening to Canadian homeowners right now.png | 1064 | TEXT OK |
| AskRoss.ca - Why is waiting for the market to recover a risky strategy.png | 919 | TEXT OK |

Bottom-line image (`AskRoss.ca - Advice from Ross Taylor Mortgages_...`) is the reusable pool image and was already confirmed to have text via the pixel count above.

---

### Check 6: RGB mode (no alpha) — PASS

All 17 output images are saved as RGB mode (no alpha channel). None are RGBA.

| Category | Files checked | All RGB |
|----------|---------------|---------|
| Root (Feature, RAW, Banner, Mobile) | 4 | Yes |
| Article images | 9 | Yes |
| GMB images | 4 | Yes |

---

### Check 7: Folder structure — PASS

Required folder structure is fully present:

```
out/test-output/Blog Images - Should You Sell Your Home Before Things Get Worse/
├── Feature Image - Should You Sell Your Home Before Things Get Worse.png          OK
├── Should You Sell Your Home Before Things Get Worse - Feature Background RAW.png OK
├── Banner - Should You Sell Your Home Before Things Get Worse.png                 OK
├── Mobile - Should You Sell Your Home Before Things Get Worse.png                 OK
├── BLOG POST - Large Article Images for Askross.ca/                               OK (9 files)
└── BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/                               OK (4 files)
```

---

## Ground Truth Comparison

Compared test output against `(1) Complete Blog Article Images Sample/` (ground truth from a previously completed blog article).

Note: ground truth uses a different article title ("Why Are Global Events Driving the Bank of Canada Rate Hold?") and real photo backgrounds; test output uses Phase 1 solid-color backgrounds. Comparison is structural (dimensions, color mode, overlay presence) — not pixel-identical.

| Category | Test file | GT file | Dims match | Mode match | Notes |
|----------|-----------|---------|------------|------------|-------|
| Feature Image | Feature Image - Should You Sell... | Feature Image - Why Are Global Events... | 700x450 = 700x450 YES | RGB = RGB YES | Test uses solid bg (Phase 1); GT uses real photo. Dimensions identical. |
| Article Image | AskRoss.ca - Advice from Ross Taylor... | AskRoss.ca - Are prices dropping... | 1920x1080 = 1920x1080 YES | RGB = RGB YES | Both have overlay in top-left corner — consistent. |
| GMB Image (Toronto) | Toronto - Should You Sell... | Toronto - Why Are Global Events... | 1200x900 = 1200x900 YES | RGB = RGB YES | Dimensions match; GMB logo in mid-left for both. |
| Banner | Banner - Should You Sell... | Banner - Why Are Global Events... | 1286x300 = 1286x300 YES | RGB = RGB YES | Both have overlay detected. |

**Ground truth comparison: PASSED** — all structural checks consistent between test output and ground truth.

---

## Notes on QA Check Design

### Overlay detection methodology
The initial overlay check (comparing pixel (20,20) vs pixel (960,540)) was found to be incorrect for this pipeline because the overlay is a **uniform semi-transparent scrim**: both the logo corner and the center of the image receive the same darkening, so the top-left vs center difference is 0 even when the overlay IS correctly applied.

The corrected detection uses:
1. For solid Phase 1 backgrounds: confirm that pixel values differ from the known raw background color (dist_from_raw >= 5), AND confirm white/light logo pixels exist in the image-specific logo region.
2. For high-variance backgrounds (real photos or reusable pool images): confirm light pixels exist in the image-specific logo region.
3. Logo regions differ by image type: article images have the logo in the top-left (Y=20–90, X=20–230); GMB images have the logo in the mid-left (Y=456–686, X=236–422).

### Text detection methodology
The initial text check (scanning rows 400–900) missed text that was placed at rows 200–310 by the auto-text-position algorithm. Phase 1 solid-color backgrounds have uniform luminance, so `auto_text_position()` consistently picks "upper-left" which places text at Y≈200. The corrected check scans the entire image below the logo band (Y=100+).

---

## Issues Found

None. All 7 checks pass, ground truth comparison passes, 17/17 files validated.

---

## Verdict

**Phase 1: PASSED** — all 7 QA checks pass, 17 files validated, ground truth structural comparison passes.

The pipeline correctly produces:
- Exact pixel dimensions across all 5 image types
- Correct folder structure and file naming
- Overlay compositing applied to all images requiring it
- White text rendered on all non-bottom-line article images
- All outputs saved as RGB (no alpha channel)
- Feature Background RAW saved as clean uniform background (no overlay, as required)
