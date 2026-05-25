# Blog Image Creation — End-to-End Process

From receiving an article to delivering final images.

---

## Step 1 — Read the Article and Build the Manifest

You provide the article. I extract:

- **Title** (H1) — drives all filenames, feature image, banners, GMB
- **Every H2 heading in order** — each becomes one large article image
- **Which H2 is the bottom-line** — the "Advice from Ross Taylor Mortgages" closer
- **Which H2 is the FAQ** — the "List of all FAQs" section
- **Theme label** — chosen from: Housing News, Mortgage Rates, Renewal Tips, Refinancing, Buyer's Guide, Financial Advice, Market Update
- **GMB cities** — default Toronto, Ottawa, Richmond Hill, Mississauga

All of this is written into `out/manifest.json`. Article image filenames are numbered sequentially:
```
AskRoss.ca - 1 - {H2 title}.png
AskRoss.ca - 2 - {H2 title}.png
...
```

**Key question at this step:** Is this a selling article? ("sell", "selling", or "for sale" in the title). This changes the entire background strategy for feature, banners, GMB, and bottom-line.

---

## Step 2 — Generate Backgrounds

### Selling articles
Feature image, banner, mobile, GMB, and bottom-line all use the prebuilt **home for sale pool**:
```
references/BLOG POST - Large Article Images for Askross.ca/
  Reusable Image Large Article Image Assets/home for sale options/
```
**Recommended:** Pool 1 (`home for sale.png`) — FOR SALE sign as hero, always in frame. Pool 7 (`home for sale (7).png`) — home + sign, no family, clean alternative.

Article section backgrounds are still generated normally.

### All articles — section backgrounds
Run `generate_gemini.py` (AI via Gemini 2.5 Flash) or `generate_phase2.py` (Pexels stock photos).

Each H2 section gets a contextually relevant background:

| Section topic | Approach | Mode |
|---|---|---|
| Equity / underwater | House model sinking, empty piggy bank | OBJECT |
| Mortgage renewals | Renewal letter on kitchen counter | OBJECT |
| Credit score | Laptop showing credit score gauge | OBJECT |
| Waiting / time | Hourglass on calendar | OBJECT |
| Financial reset | Couple reviewing budget together | PEOPLE |
| Warning signs | Red flag markers in grass | OBJECT |
| Homeowners affected | Couple at kitchen table with documents | PEOPLE |
| Bottom-line | Contextual to article topic | PEOPLE or OBJECT |
| **FAQ** | **Fixed pool image only — never generate** | — |

**Gemini prompt rules (every prompt must include):**
1. Scene mode: OBJECT / PEOPLE / PLACE
2. Subject framing: focal point on upper-third horizontal line, 35–55% of frame height
3. Upper-left quiet zone: ~260×100px must be clear for logo overlay
4. Current Canadian season — never use autumn foliage in spring/summer
5. No text, logos, watermarks in generated image
6. Avoidance list: face staring at camera, cropped heads, distorted hands, AI artifacts, 3D render style, wrong-season foliage

Raw backgrounds saved to `out/generated/`.

---

## Step 3 — Review Outputs

Examine each generated/fetched background:

| Folder | Criteria |
|---|---|
| `good/` | Right subject, clean composition, no AI artifacts, suits the section |
| `close but not/` | Right concept, wrong framing, title wraps to 3 lines, sign cut off |
| `no/` | Wrong subject, overdramatic, wrong season, face staring at camera |

If something isn't right, regenerate just that section with a refined prompt, swap to Pexels, or try a different scene mode.

---

## Step 4 — Composite the Article Images (1920×1080)

Using approved backgrounds, each article image is built:

1. `resize_and_center_crop(background, 1920, 1080)`
2. Apply overlay: `(1) AskRoss.ca - Just logo and grey overlay.png`
3. Render H2 title text with drop shadow

**Typography:**
- Font: Archivo Black, 60px, white
- Line height: 75px (60px + 15px leading)
- Drop shadow: 1px offset, GaussianBlur radius 3, 45% opacity
- Max width: 1300px (left positions) / 1400px (center position)
- Preferred wrap: 2 lines, top line longer than second, no single-word last line

**Text position alternates automatically by section index (0-based):**
```
Section 1 → lower-left
Section 2 → center
Section 3 → lower-left
Section 4 → center   ...and so on
```

**Special sections:**
- **Bottom-line:** Logo-only overlay (`(8) Rule - AskRoss.ca - For The Closer...`). **No text ever.**
- **FAQ:** Fixed pool image, resized to 1920×1080. **No overlay. No text ever.**

---

## Step 5 — Build Feature, Banners, and GMB

All four formats share the same background image.

### Feature Image — 700×450
1. Resize/center-crop background to 700×450
2. Save RAW version (no overlay — reusable asset)
3. Auto-select 2-line or 3-line overlay based on actual title wrap
4. Render theme label: Aleo Bold 13px, ALL CAPS, x=138, y=280
5. Render article title: Open Sans Bold 700, 20px, ALL CAPS, x=138, y=299, max 440px wide

### Desktop Banner — 1286×300
- Photo + overlay only. **No text ever.**
- For sign-based images: use red pixel detection to find sign position, center crop on it

**Crop math (1920×1080 source):** scales to 1286×723, valid crop range `top=0–423`

```python
# Find FOR SALE sign before cropping
red_mask = (arr[:,:,0] > 150) & (arr[:,:,1] < 80) & (arr[:,:,2] < 80)
sign_center_scaled = int(np.median(np.argsort(red_mask.sum(axis=1))[-20:]) * scale)
top = max(0, min(sign_center_scaled - 150, 423))
# Then nudge based on visual review
```

**Pool 1 approved value:** `top=239`

### Mobile Banner — 400×600
- Photo + overlay only. **No text ever.**
- Portrait crop from landscape source: scales to 1067×600, adjust `left` to frame the sign

**Pool 1 approved value:** `left=566` (100px left of far right)

### GMB Share Images — 1200×900 × 4 cities
- City overlay (Toronto / Ottawa / Richmond Hill / Mississauga) applied via alpha composite
- Article title rendered: Open Sans Bold 700, 35px, ALL CAPS, 1px letter spacing, 1.3× line height, x=236, y=573, max 850px

---

## Step 6 — Fine-Tune

Review and apply targeted fixes:

| Issue | Fix |
|---|---|
| Title position wrong | Recomposite with different `force_position` |
| Title Y off | Recomposite with `text_y + 5` (center position needs +5px visual correction) |
| Background not right | Regenerate just that section |
| Want an alternative | Generate ALT version with suffix in filename — never replace the original |
| Banner/mobile crop off | Adjust `top` or `left` offset until sign is fully in frame |

---

## Step 7 — Final Selection

Confirm all keepers into `out/final selection/`:

```
final selection/
├── Feature Image - {title}.png                 700×450
├── Banner - {title}.png                        1286×300
├── Mobile - {title}.png                        400×600
├── AskRoss.ca - 1 - {H2}.png                  1920×1080
├── AskRoss.ca - 2 - {H2}.png
├── ... (all regular sections)
├── AskRoss.ca - N - Advice from Ross Taylor Mortgages_ ...png   (bottom-line)
├── AskRoss.ca - N+1 - List of all FAQs_ ...png                  (FAQ)
├── AskRoss.ca - X ALT WARNING - {H2}.png       (approved alternatives)
└── BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/
    ├── Toronto - {title}.png                   1200×900
    ├── Ottawa - {title}.png
    ├── Richmond Hill - {title}.png
    └── Mississauga - {title}.png
```

---

## Step 8 — Archive and Clean Up

```
out/
├── final selection/        ← PNG masters
├── final selection - JPEG/ ← delivery copies (created in Step 9)
├── generated/              ← raw backgrounds (kept for reruns)
├── manifest.json
└── _archive/               ← everything else
    ├── Blog Images - {title}/
    ├── Blog Images - AI Generated - {title}/
    ├── BEST - {title}/
    └── test-output/
```

---

## Step 9 — JPEG Conversion (Final Standardization Step)

Always the last step. Convert the entire final selection to JPEG for delivery:

```python
from src.compositors.shared import convert_folder_to_jpeg

convert_folder_to_jpeg(
    src_dir="out/final selection",
    dst_dir="out/final selection - JPEG",
    quality=95,
)
```

- **PNG** = working / archival format (keep)
- **JPEG** = delivery format (upload / send to client)
- Mirrors exact subfolder structure including GMB folder
- Quality 95 = visually lossless at web display sizes

---

## Deliverable Summary

| Format | Dimensions | Count |
|---|---|---|
| Large Article Images | 1920×1080 | 1 per H2 section |
| Feature Image | 700×450 | 1 |
| Desktop Banner | 1286×300 | 1 |
| Mobile Banner | 400×600 | 1 |
| GMB Share Images | 1200×900 | 4 (one per city) |
| **Total** | | **~16–18 images** |

All delivered in both PNG and JPEG.
