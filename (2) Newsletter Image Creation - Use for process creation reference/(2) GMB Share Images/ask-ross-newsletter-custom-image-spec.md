# Ask Ross Newsletter — Custom Image Spec

**For:** Raven AI agent (Claude Code) — when you supply your own image
**Output:** Two PNGs in `out/` — 1200 × 900 GMB Share and 1200 × 638 Banner
**Script:** `build_newsletter_custom.py`
**When to use:** You have a specific photo you want as the hero — a news screenshot, a branded headshot, an event photo, a screengrab from a news broadcast, or any image you own or have rights to use

---

## When to use this workflow vs. the others

| Use Custom (`build_newsletter_custom.py`) | Use AI (`build_newsletter.py`) | Use Pexels (`build_newsletter_pexels.py`) |
|---|---|---|
| You have a specific image in hand | No image — let AI generate one | No image — search stock library |
| News screenshots (CBC, CTV, Globe) | Lifestyle/seasonal/editorial scenes | Generic stock photos |
| Branded event photos | Abstract or Canadian setting imagery | When a real photo exists on Pexels |
| Headshots of real people you have rights to | Any topic without a real-world subject | News topics without a strong match |

---

## Step 1 — Drop the image into `in/`

Save your image to the `in/` folder inside GMB Image Builder:

```
GMB Image Builder/
└── in/
    └── your-image.jpg   ← drop it here
```

Any common format works: `.jpg`, `.jpeg`, `.png`, `.webp`. The script will center-crop and resize it to 1200×638 automatically.

**Tip:** If the subject is off-center after the default crop, use `--banner-zoom` to pull in closer, or rename the file with a short descriptive slug (e.g., `mark-carney-interview.jpg`) to keep `out/` tidy.

---

## Step 2 — Prepare the text fields

Extract from the newsletter:

| Field | Rule | Max chars |
|---|---|---|
| `title1` | Lead article headline or issue title | **55 characters** |
| `title2` | Always `\| Ask Ross Newsletter` — never change | n/a |
| `intro` | 2–3 sentence summary of the issue's key topics. No em dashes. | **245 characters** |

**Title1 examples:**
- `"Mark Carney's Win: What It Means for Housing"` (45 chars) ✓
- `"What the Election Result Means for Your Mortgage"` (49 chars) ✓

**Intro rules:**
- Maximum 245 characters
- No em dashes (`—`) or en dashes (`–`) — use ` - ` instead
- Hard-capped at 3 lines regardless of character count
- Line 2 must be the longest line — script auto-balances (short / long / short shape)
- Line 3 minimum 3 words — script auto-enforces; line 3 can have more than 3 words

---

## Step 3 — Run the build script

The issue folder (`out/{issue-folder}/`) must exist before running. Pass it via `--output-dir`.

```bash
python build_newsletter_custom.py \
  --banner-image "out/{issue-folder}/{name} Banner Raw.png" \
  --title1 "Mark Carney's Win: What It Means for Housing" \
  --intro "Canada has a new PM and housing is front and center. From GST breaks for first-time buyers to 4 million new homes by 2035, here's what Carney's win means for you." \
  --output-dir "out/{issue-folder}"
```

### Flags

| Flag | Purpose |
|---|---|
| `--banner-image PATH` | Path to your image (relative to script dir, or absolute) |
| `--reuse-banner` | Skip image load, reuse the cached Banner PNG. Use for text/layout tweaks. |
| `--banner-zoom 1.2` | Zoom into the lower portion of the banner (1.0 = no zoom) |
| `--title2` | Override only if rebranding. Default: `\| Ask Ross Newsletter` |
| `--output` | Override output path. Default: derived from title1. |

**When to use `--reuse-banner`:** Any time you are only adjusting text content or layout — do NOT reload and re-crop the source image. Only re-run the full load when using a new image or adjusting zoom.

---

## Output filenames (auto-derived from title1)

All files land in the issue folder set by `--output-dir "out/{issue-folder}"`.

| File | Naming rule |
|---|---|
| GMB Share image | `out/{issue-folder}/{title1} GMB Share.png` |
| Banner only | `out/{issue-folder}/{title1} Banner.png` |

Colons in title1 become ` - ` for Windows filename compatibility.

---

## Composition tips

| Issue | Fix |
|---|---|
| Subject cropped out (too much background) | Add `--banner-zoom 1.2` to 1.3 |
| Subject too far left or right | Zoom in until they're centred |
| Image too dark under overlay | Use a brighter source image |
| Upper-left logo area is cluttered | Crop tighter with zoom so subject moves right |

---

## Layout constants (locked — same across all workflows)

Canvas: **1200 × 900 px**, RGB output.

| Element | Top (px) | Left (px) | Max width (px) | Notes |
|---|---|---|---|---|
| BANNER region | 0 | 0 | 1200 × 638 | Your supplied photo |
| OVERLAY | 0 | 0 | 1200 × 900 | ask-ross-overlay.png composited on top |
| TITLE1 | 661.72 | 230 | 899 | Single line, left-aligned |
| TITLE2 | 704.79 | 230 | 466 | Single line, left-aligned |
| INTRO | 761.44 | 112 | 1010 | Wraps, hard-capped at 3 lines |

### Typography (locked)

| Element | Font file | Size (px) | Color |
|---|---|---|---|
| TITLE1 | `Aleo-Regular.ttf` | 35 | `#1A1A1A` |
| TITLE2 | `Aleo-Regular.ttf` | 35 | `#1A1A1A` |
| INTRO | `OpenSans-Regular.ttf` | 27 | `#4A4A4A` |

INTRO line height: **40 px**

---

## Quality checks (automatic)

1. Output dimensions exactly `(1200, 900)`
2. White band — pixel at `(600, 800)` is `(255, 255, 255)`
3. Banner visible — pixel at `(600, 300)` is not pure black
4. TITLE1 rendered — pixel at `(300, 680)` is not pure white
