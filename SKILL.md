# Blog Article Image Creation Skill

Generates a complete set of blog article images for AskRoss.ca from a markdown or WordPress HTML article file.

---

## What it produces

For every article, the skill outputs:

| File | Dimensions | Description |
|---|---|---|
| `Feature Image - {title}.png` | 700×450 | WordPress featured image with overlay |
| `{title} - Feature Background RAW.png` | 700×450 | Clean background (no overlay) — reusable |
| `Banner - {title}.png` | 1286×300 | Desktop blog banner |
| `Mobile - {title}.png` | 400×600 | Mobile blog banner |
| `BLOG POST - Large Article Images.../AskRoss.ca - {H2}.png` | 1920×1080 | One per H2 section |
| `BLOG RESHARE - GMB - .../Toronto - {title}.png` | 1200×900 | GMB share image ×4 cities |

---

## Quick start

```bash
# Phase 1 — test pipeline (no API calls)
python run.py --article "Should You Sell Your Home Before Things Get Worse.md" --phase1

# Phase 2 — real generation (requires OPENROUTER_IMAGE_API_KEY in .env)
python run.py --article "My Article.md" --phase2
```

---

## Architecture

```
src/
├── parser/parse_article.py         — extracts H2 sections, section numbers, metadata
├── prompts/prompt_builder.py       — Art Director prompts per H2 (16:9 blog format)
├── prompts/feature_prompt_builder.py — feature/banner/GMB shared background prompt
├── compositors/
│   ├── shared.py                   — resize_and_center_crop, apply_overlay, draw_text_with_shadow
│   ├── compose_article_images.py   — 1920×1080 article images
│   ├── compose_feature.py          — 700×450 feature + RAW
│   ├── compose_banners.py          — 1286×300 desktop + 400×600 mobile
│   ├── compose_gmb.py              — 1200×900 ×4 cities
│   └── create_folder_structure.py  — output folder layout
└── qa/
    ├── validate.py                 — 7-check validation suite
    └── compare_ground_truth.py     — structural comparison vs ground truth
```

---

## Image types and compositing rules

### Article images (1920×1080)
- **Regular H2:** generated background → standard overlay (logo + gray scrim) → Archivo Black 48px white title text → auto-positioned (luminance analysis)
- **Bottom-line H2** (contains "bottom line" or "advice from ross taylor"): random reusable background from pool → logo-only overlay → **no text**
- **FAQ H2** (contains "faq"): random reusable background from pool → standard overlay → title text rendered

### Feature / Banner / GMB (shared background)
One background image is generated for the entire article. It is cropped to each target size:
- Feature: center crop 700×450
- Desktop banner: center crop 1286×300
- Mobile: center crop 400×600
- GMB ×4: center crop 1200×900

Each gets its own overlay template applied after cropping.

---

## Overlay templates used

| Image type | Overlay path |
|---|---|
| Article image | `BLOG POST - Large Article Images for Askross.ca/(1) AskRoss.ca - Just logo and grey overlay.png` |
| Bottom-line | `BLOG POST - Large Article Images for Askross.ca/(8) Rule - AskRoss.ca - For The Closer - No Overlay - Just Logo.png` |
| Feature (2-line) | `BLOG POST - Feature Image/Feature image - Use this is title is two lines - overlay.png` |
| Feature (3-line) | `BLOG POST - Feature Image/Feature image - use this if title is three lines - overlay.png` |
| Desktop banner | `BLOG POST - Banner Images/Banner - Title of Article - Overlay.png` |
| Mobile banner | `BLOG POST - Banner Images/MOBILE - Title of Article - Overlay.png` |
| GMB (per city) | `BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/{City} - Title.png` |

---

## Reusable assets

Bottom-line and FAQ images pull from pre-made backgrounds in:
```
BLOG POST - Large Article Images for Askross.ca/Reusable Image Large Article Image Assets/
```
- Bottom-line pool: `AskRoss.ca - Bottom line or Advice from Ross Taylor Mortgages*.png`
- FAQ pool: `AskRoss.ca - All of the FAQs in this article*.png`

Selection is random each run.

---

## Typography

| Image type | Font | Size | Color | Shadow |
|---|---|---|---|---|
| Article images | Archivo Black | 48px | #FFFFFF | offset 1px, blur 3, opacity 114 |
| Feature / banners / GMB | Archivo Black | auto-fitted | #FFFFFF | offset 1px, blur 3, opacity 114 |

Font path: `(2) Newsletter Image Creation - Use for process creation reference/(1) Banner Images/fonts/Archivo_Black/ArchivoBlack-Regular.ttf`

---

## Prompt system (Phase 2)

Prompts follow the Art Director spec adapted for 16:9 1920×1080:
- **Literal** to H2 topic (stressed homeowner with notice → that exact scene)
- Canadian setting markers (Toronto neighborhoods, Bank of Canada Ottawa, etc.)
- Upper-left ~260×100px kept visually quiet for logo overlay
- Lower-center space for title text
- 70–110 words, ends with negatives list
- Bottom-line and FAQ sections return `None` (use reusable images, no generation needed)

---

## Parser rules

Supported formats: **Markdown** and **WordPress Gutenberg HTML**

- Skips subtitle H2s that appear before the "Jump to a specific section" navigation block
- Extracts section numbers from `<figure id="N">` (HTML) or assigns sequentially from 2 (markdown)
- Detects bottom-line sections: text contains "bottom line" or "advice from ross taylor"
- Detects FAQ sections: text contains "faq" or "list of all faqs"
- Filename sanitization: removes `?`, replaces `: ` with `_ `, removes illegal chars

---

## QA suite

Run after any output:
```bash
python -c "
from src.qa.validate import run_all_checks
result = run_all_checks('out/test-output/Blog Images - {title}', '(1) Complete Blog Article Images Sample')
print(result)
"
```

7 automated checks: dimensions, file count, naming convention, overlay presence, text presence, RGB mode, folder structure.

---

## Phase 2 Gutenberg output

After compositing, `run.py --phase2` also writes:
- `out/gutenberg-blocks.html` — WordPress `<!-- wp:image -->` blocks with `id="{section_number}"` on each `<figure>`, TOC HTML with anchor links, alt text `AskRoss.ca - {H2 text}`
- `out/manifest-final.json` — final manifest with all generated image paths

---

## Environment variables (.env)

| Key | Used by |
|---|---|
| `OPENROUTER_IMAGE_API_KEY` | Article image generation (Gemini 2.5 Flash Image) |

The `.env` file is loaded from the working directory root, with fallback to `(2) Newsletter Image Creation - Use for process creation reference/.env`.
