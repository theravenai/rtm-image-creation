# Ask Ross Newsletter — Banner Image Spec

**For:** Raven AI agent (Claude Code) — newsletter feature banner workflow
**Output:** Two PNGs in `out/` — 1200 × 800 Banner Raw + 1200 × 800 Banner
**Script:** `build_newsletter_banner.py`
**When to use:** Every newsletter issue. Build the banner FIRST. GMB Share is made afterward from the Banner Raw.

---

## Full workflow (every issue)

```
Step 0 — Create the issue output folder (FIRST THING — before any script)
    mkdir "out/{issue-folder}"
    All script calls for this issue append: --output-dir "out/{issue-folder}"

Step 1 — Build banner image
    → out/{issue-folder}/{name} Banner Raw.png   (1200×800, no overlay, no text — used for GMB Share later)
    → out/{issue-folder}/{name} Banner.png       (1200×800, overlay + text if appropriate — send for approval)

Step 2 — Operator approves banner

Step 3 — Build GMB Share (using the approved Banner Raw)
    python build_newsletter_custom.py \
        --banner-image "out/{issue-folder}/{name} Banner Raw.png" \
        --title1 "..." --intro "..." \
        --output-dir "out/{issue-folder}"
```

**Never start the GMB Share before the banner is approved.**

---

## Decision: which image source?

| Newsletter topic | Source |
|---|---|
| Named politician (Carney, Trump) or major world event | `--source sonar` |
| You have a specific photo | `--source custom` |
| Lifestyle, seasonal, abstract, housing/rates/mortgage topic | `--source ai` |
| Generic topic, no strong news hook | `--source pexels` |

---

## Decision: add text or not?

| Subject in image | Rule |
|---|---|
| Ross Taylor (the face of Ask Ross) | **No text** — he speaks for himself |
| Named politician (Carney, Trump, etc.) | **No text** — image is self-explanatory |
| Powerful editorial photo (striking scene, clear story) | **No text** — let the image breathe |
| Abstract, lifestyle, conceptual, scene-setting — no prominent person | **Center text** |
| Scene with people in lower half, open sky/space above | **Upper-left text** |
| Scene with people in upper half, open ground/space below | **Lower-left text** |

The script auto-decides based on `--sonar-query`, `--pexels-query`, or `--name`. Override any time:
- `--no-text` — force no text
- `--text` — force text on
- `--subject-hint "Trump"` — explicit hint for auto-decision

---

## Title writing rules (SEO + AI optimized)

Banner titles are **not** the newsletter's title1. They are a separate hook written to:

1. **Form a natural-language question** an average Canadian user would type into Google
2. **Be clickbaity** — make the reader want to open the article just from the title alone
3. **Include relevant keywords** — Canadian housing, mortgage, rates, real estate, etc.
4. **Be specific to the newsletter content** — not generic filler

| Good (SEO question, clickbait) | Too plain |
|---|---|
| "Is Now the Right Time to Buy a Home in Canada?" | "Spring Housing Market" |
| "What the Bank of Canada Didn't Say About Rates" | "Rate Decision" |
| "Are Canadian Home Prices Finally Coming Down?" | "Fall Market Update" |
| "Should You Lock In Your Mortgage Rate Right Now?" | "Mortgage Rate News" |

**Capitalisation:**
- **Question titles:** Sentence case only — capitalize the first letter of the first word, plus any proper nouns (names, places, brands). Everything else lowercase.
  - ✓ `"Is now the right time to buy a home in Canada?"`
  - ✓ `"What the Bank of Canada didn't say about rates"`
  - ✗ `"Is Now The Right Time To Buy A Home In Canada?"` ← title case, wrong for questions
- **Statement titles:** Title case is acceptable for punchy statements that are not questions.
  - ✓ `"Your Spring Advantage: Play the Market Before It Plays You"`

**Character count:** Aim for 40–60 characters (wraps to 2 clean lines at 45px). Hard cap: 80 characters (3 lines max). Never leave a single word on the last line.

---

## Typography (locked)

- **Font:** Archivo Black (`fonts/Archivo_Black/ArchivoBlack-Regular.ttf`)
- **Size:** 45px
- **Color:** white `#FFFFFF`
- **Line height:** 55px (45px font + 10px leading)
- **Drop shadow:**
  - Colour: `#000000` black
  - Opacity: 45% (Photoshop setting)
  - Angle: 40° (Use Global Light)
  - Distance: 1px
  - Spread: 0%
  - Size: 6px (PIL GaussianBlur radius = 3)

---

## Text position rules (locked)

### Upper-left — `--text-position upper-left`
- **Y position:** 213px from top
- **When to use:** Subjects (people) are in the lower half of the frame. Text sits in the upper-left open space above their heads.
- **Subject rule:** Bottom of text block must clear all faces. At y=213 with 2 lines (110px tall), text ends at y≈323 — safe for subjects standing in the lower-center of a 800px image.
- **Example:** Couple in front of a house (lower-center) → title in upper-left above them.

### Lower-left — `--text-position lower-left`
- **Y position:** Lower third (text top at y≈550 for 2 lines)
- **When to use:** Subjects are in the upper portion of the frame; lower area is quiet/open.
- **Subject rule:** Text sits at y≈550+, well below where faces appear in upper-composition shots.
- **Example:** Aerial shot, skyline, wide landscape with sky above and open foreground below.

### Center — `--text-position center`
- **Y position:** Vertically centered (auto-calculated)
- **When to use:** No prominent human subjects. Abstract, conceptual, or scene images with open space throughout (for sale signs, landscapes, aerials, interiors).
- **Subject rule:** Only use center when there are no people in the frame, or subjects are very small/peripheral.
- **Example:** "For Sale" sign on a lawn, aerial neighbourhood view, abstract housing graphic.

### No text — `--no-text`
- **When to use:** Ross Taylor photos, named politicians, powerful editorial news photos where the image tells the story on its own. Adding text would distract or feel redundant.
- **Example:** Mark Carney press conference photo, Ross headshot, striking war/election image.

---

## Faces rule (absolute — never break)

**Text must never overlap a subject's face.**

- If you cannot find a text position that avoids faces, use `--no-text`.
- When using `upper-left` and subjects are tall (faces near y=200–300), move text further up or switch to `lower-left`.
- Center text is only for images without prominent people — never use it on a portrait or people-forward shot.

---

## Text layout constants (in script)

| Constant | Value | Notes |
|---|---|---|
| `FONT_SIZE` | 45 | Archivo Black |
| `TEXT_LEFT_MARGIN` | 193 | Just right of logo box (logo spans x=17–190) |
| `TEXT_MAX_WIDTH_LEFT` | 800 | Left-aligned positions |
| `TEXT_MAX_WIDTH_CENTER` | 900 | Center position |
| `TEXT_LINE_HEIGHT` | 55 | 45px font + 10px leading |
| `UPPER_LEFT_Y` | 213 | Top of text block for upper-left |
| `LOWER_LEFT_BOTTOM_PAD` | 140 | Bottom anchor; text_y≈550 for 2 lines |
| `SHADOW_OFFSET` | 1 | Distance: 1px (Photoshop) |
| `SHADOW_BLUR` | 3 | Size: 6px → PIL radius 3 |
| `SHADOW_OPACITY` | 114 | 45% opacity (0.45 × 255) |

---

## Step-by-step commands

### Source: Sonar (politician / world event)

```bash
# 1. Browse candidates
python build_newsletter_banner.py --source sonar \
  --sonar-query "Mark Carney 2025" --list-images --recency week

# 2. Build — no text for politician
python build_newsletter_banner.py --source sonar \
  --sonar-query "Mark Carney 2025" --use-cache --image-index 1 \
  --name "Carney Housing Win" --no-text
```

### Source: AI (lifestyle / abstract / housing topic)

```bash
python build_newsletter_banner.py --source ai \
  --banner-prompt "<Art Director output>" \
  --name "Fall Market Crossroads" \
  --title "Are Canadian Home Prices Finally Coming Down?" \
  --text-position upper-left
```

Use the Art Director prompt template from `ask-ross-newsletter-agent-spec.md`. Banner is 1200×800 — use `16:8 wide aspect` in the prompt.

### Source: Pexels (stock photo)

```bash
# 1. Browse
python build_newsletter_banner.py --source pexels \
  --pexels-query "spring Canada neighbourhood real estate" --list-photos --name preview

# 2. Build with center text (no people in shot)
python build_newsletter_banner.py --source pexels \
  --pexels-query "spring Canada neighbourhood real estate" --photo-index 9 \
  --name "Spring 2025 Market" \
  --title "Is Now the Right Time to Buy a Home in Canada?" --text-position center

# 3. Build no-text version of same image
python build_newsletter_banner.py --source custom \
  --banner-image "out/Spring 2025 Market Banner Raw.png" \
  --name "Spring 2025 Market No Text" --no-text
```

### Source: Custom (your own photo)

```bash
python build_newsletter_banner.py --source custom \
  --banner-image "in/ross-photo.jpg" \
  --name "Ross Event July" --no-text
```

---

## Text/layout tweaks (no re-fetch)

```bash
python build_newsletter_banner.py --source custom \
  --banner-image "in/photo.jpg" --name "Fall Market" \
  --reuse-raw \
  --title "What the Bank of Canada Didn't Say About Rates" \
  --text-position upper-left
```

`--reuse-raw` skips all image fetching and reuses the saved Banner Raw. Use for any title or position changes.

---

## All flags

| Flag | Purpose |
|---|---|
| `--source` | `ai` / `sonar` / `pexels` / `custom` — required |
| `--name` | Output filename stem (e.g. `"Fall Market Crossroads"`) — required |
| `--banner-prompt` | `[ai]` Image generation prompt |
| `--sonar-query` | `[sonar]` Perplexity search query |
| `--recency` | `[sonar]` `day`/`week`/`month`/`year` (default: month) |
| `--image-index N` | `[sonar]` Which candidate to use |
| `--image-count N` | `[sonar]` How many candidates to fetch (default 10) |
| `--list-images` | `[sonar]` Print candidates and exit |
| `--use-cache` | `[sonar]` Reuse candidate list from `--list-images` |
| `--pexels-query` | `[pexels]` Pexels search query |
| `--photo-index N` | `[pexels]` Which photo to use (default 0) |
| `--photo-count N` | `[pexels]` How many results to fetch (default 15) |
| `--list-photos` | `[pexels]` Print results and exit |
| `--banner-image PATH` | `[custom]` Path to image file |
| `--title TEXT` | Banner hook headline (SEO question format, 40–60 chars) |
| `--text-position` | `upper-left` / `lower-left` / `center` (default: auto) |
| `--text` | Force text on |
| `--no-text` | Force text off |
| `--subject-hint TEXT` | Hint for auto no-text detection (e.g. `"Trump"`) |
| `--banner-zoom 1.2` | Zoom into lower portion of image (1.0 = none) |
| `--reuse-raw` | Skip image fetch, reuse existing Banner Raw |
| `--output-dir PATH` | Override output directory (default: `out/`) |

---

## Output files (auto-derived from --name)

All files land in the issue folder set by `--output-dir "out/{issue-folder}"`.

| File | Purpose |
|---|---|
| `out/{issue-folder}/{name} Banner Raw.png` | 1200×800, no overlay, no text — input for GMB Share |
| `out/{issue-folder}/{name} Banner.png` | 1200×800, overlay + text — the final banner for approval |
| `out/{issue-folder}/{name} Banner Credits.txt` | Source credit (Sonar / Pexels only) |

---

## Canvas spec (locked)

- Canvas: **1200 × 800 px**, RGB output
- Overlay: `(1) Banner Images/Logo + Grey Transparent Layer - Banner.png`
- Logo position in overlay: x=17–190, y=20–65 (top-left)
- Text left margin: **x=193** (just right of logo box, never further left)

---

## QC (automatic)

1. Output dimensions exactly `(1200, 800)`
2. Center pixel `(600, 400)` is not pure black (banner not blank)
