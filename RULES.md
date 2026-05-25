# Blog Article Image Creation — Rules (Never Break These)

**Ground truth reference:** `references/(1) Complete Blog Article Images Sample/`
**SOP reference:** `SOP_ Create Blog Article Images and Social Share Assets.pdf`
**Newsletter reference:** `references/(2) Newsletter Image Creation - Use for process creation reference/`

---

## Locked-in Template Summary (do not deviate without user re-approval)

| Image type | Canvas | Font | Size | Key rule |
|---|---|---|---|---|
| Large Article Image | 1920×1080 | Archivo Black | 60px | Auto text position via luminance |
| Feature Image — Theme | 700×450 | Aleo Bold | 13px ALL CAPS | 1px letter spacing, x=138, y=280 |
| Feature Image — Title | 700×450 | Open Sans Bold 700 | 20px ALL CAPS | 0px spacing, 1.3× line height, max 440px, y=299 |
| Desktop Banner | 1286×300 | — | — | NO TEXT, photo only |
| Mobile Banner | 400×600 | — | — | NO TEXT, photo only |
| GMB Share Image | 1200×900 | Open Sans Bold 700 | 35px ALL CAPS | 1px letter spacing, 1.3× line height, max 850px |

**Universal typography rules:**
- Top line of any title must be longer than the second line
- Never a single word on the last line (widow prevention — enforced in code automatically)
- Overlays must be semi-transparent so real photo backgrounds show through

---

## Theme Label Derivation Process (Feature Image)

The theme label appears above the article title on the Feature image (e.g. "HOUSING NEWS").

**Priority order:**
1. **Set explicitly in `manifest.json`** as `"theme_label": "Housing News"` — always wins. This is the required step when parsing a new article.
2. **Keyword fallback** in `_derive_theme_label()` (`run.py`) — used only if manifest has no theme_label:
   - "Bank of Canada" / "interest rate" / "rate cut" / "rate hike" → **Mortgage Rates**
   - "renew" / "renewal" / "payment shock" → **Renewal Tips**
   - "refinanc" / "heloc" / "equity" → **Refinancing**
   - "buy" / "buyer" / "first-time" / "purchase" → **Buyer's Guide**
   - "credit" / "debt" / "financial reset" / "budget" → **Financial Advice**
   - "market" / "home price" / "recovery" / "crash" → **Market Update**
   - Everything else → **Housing News**

**How to choose the right theme:**
- Read the full article, not just the title
- Identify the primary trend or category being addressed
- Use 2 words max (e.g. "Housing News", "Mortgage Rates", "Market Update")
- Theme is always rendered ALL CAPS regardless of how it is stored

---

## File paths (after folder reorganisation)

All overlay templates are now inside `references/`:

| Image type | Overlay path |
|---|---|
| Article image (logo + gray scrim) | `references/BLOG POST - Large Article Images for Askross.ca/(1) AskRoss.ca - Just logo and grey overlay.png` |
| Bottom-line (logo only, NO scrim) | `references/BLOG POST - Large Article Images for Askross.ca/(8) Rule - AskRoss.ca - For The Closer - No Overlay - Just Logo.png` |
| Feature 2-line title | `references/BLOG POST - Feature Image/Feature image - Use this is title is two lines - overlay.png` |
| Feature 3-line title | `references/BLOG POST - Feature Image/Feature image - use this if title is three lines - overlay.png` |
| Desktop banner | `references/BLOG POST - Banner Images/Banner - Title of Article - Overlay.png` |
| Mobile banner | `references/BLOG POST - Banner Images/MOBILE - Title of Article - Overlay.png` |
| GMB Toronto | `references/BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/Toronto - Title.png` |
| GMB Ottawa | `references/BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/Ottawa - Title.png` |
| GMB Richmond Hill | `references/BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/Richmond Hill - Title.png` |
| GMB Mississauga | `references/BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/Mississauga - Title.png` |

Reusable assets:
```
references/BLOG POST - Large Article Images for Askross.ca/Reusable Image Large Article Image Assets/
```

---

## Fonts (all from `fonts/` in working dir root)

| Font | File | Used for |
|---|---|---|
| Aleo Bold | `fonts/Aleo/static/Aleo-Bold.ttf` | Feature image THEME text |
| Open Sans Bold (700) | `fonts/Open_Sans/static/OpenSans-Bold.ttf` | Feature image TITLE + GMB title (ALL CAPS) |
| Open Sans Regular (400) | `fonts/Open_Sans/static/OpenSans-Regular.ttf` | Reserved / unused currently |
| Archivo Black | `references/(2) Newsletter Image Creation - Use for process creation reference/(1) Banner Images/fonts/Archivo_Black/ArchivoBlack-Regular.ttf` | Large article images (H2 titles) |

---

## Image type rules — never break

---

### 1. Large Article Images — 1920×1080

**Process:** Follows the newsletter banner process exactly (`references/(2) Newsletter Image Creation.../build_newsletter_banner.py`). Same compositing, same drop-shadow technique, same luminance-based auto text positioning. Canvas is larger so font scales up.

**Compositing steps:**
1. Resize/center-crop background image to 1920×1080
2. Apply overlay: `(1) AskRoss.ca - Just logo and grey overlay.png` (uniform 29% scrim + logo top-left x=24–217, y=26–80)
3. Run luminance analysis to auto-select text position (center / upper-left / lower-left)
4. Render H2 title text with drop shadow

**Typography:**
- Font: **Archivo Black** (`ArchivoBlack-Regular.ttf`)
- Size: **60px** (scaled from newsletter's 45px × 1080/800 ratio)
- Color: **white #FFFFFF**
- Line height: **75px** (60px font + 15px leading)
- Drop shadow: offset 1px (angle 40°), GaussianBlur radius 3, opacity 114/255 (45%)

**Text positioning constants:**
```python
FONT_SIZE        = 60
TEXT_LINE_HEIGHT = 75     # 60 + 15 leading
TEXT_LEFT_MARGIN = 227    # just right of logo box (logo spans x=24–217)
TEXT_MAX_WIDTH_LEFT   = 1300   # left-aligned positions — forces 2-line wrap on most H2 titles ✅ updated 2026-05-21
TEXT_MAX_WIDTH_CENTER = 1400   # center position — forces 2-line wrap on most H2 titles ✅ updated 2026-05-21
UPPER_LEFT_Y          = 284    # y=213 in newsletter × 1080/800 = 288 → 284
LOWER_LEFT_BOTTOM_PAD = 189    # 140 × 1080/800 — text_y≈700 for 2 lines
```

**Alternating text positions (locked in 2026-05-21):**
- Regular H2 sections alternate position by index (0-based):
  - Even index (0, 2, 4, 6…) → `force_position="lower-left"`
  - Odd index (1, 3, 5, 7…) → `force_position="center"`
- Use `compose_article_image(force_position=...)` — bypasses luminance analysis entirely
- Bottom-line and FAQ sections are exempt (they follow their own rules)
- Prevents consecutive same-position layouts that look repetitive

**Center text Y offset (locked in 2026-05-21):**
- Mathematical center: `text_y = (1080 - num_lines * 75) // 2 = 465` for 2 lines
- Visually the text reads as too high — apply +5px offset → `text_y = 470`
- This is applied whenever `force_position="center"` is used

**Auto text position (luminance analysis — same as newsletter):**
- Measure average luminance in 3 zones: upper-left, lower-left, center
- Pick the darkest zone → best contrast for white text
- Faces rule: text must NEVER overlap a face
- Only used when `force_position=None` (i.e. luminance mode, not alternating mode)

**Title wrapping rules (never break):**
- Prefer **2-line wrapping** for most H2 titles. The max-width constants above are calibrated to achieve this.
- Top line must be longer than or equal to the second line (natural with greedy word wrap)
- No single word on the last line — widow prevention enforced in code
- NEVER place text where it would cover a person's face. Luminance-based position selection avoids this for images where faces are in one zone; if the chosen zone has a face, prefer the next-darkest zone.

**Context rule (never break):**
- Background images must be contextually relevant to the H2 topic.
- Do NOT use a generic filler image when a more specific and relevant image exists.
- Example: an H2 about equity loss → sinking house or empty piggy bank, NOT a random home exterior.
- Example: an H2 about selling your home → home with FOR SALE sign or family in front of home listed for sale.

**Bottom-line H2 variant:**
- Background: pool images from `Reusable Image Large Article Image Assets/AskRoss.ca - Bottom line or Advice from Ross Taylor Mortgages*.png` are used for Phase 1 test only.
- **Phase 2 rule:** generate or fetch a contextually relevant background that matches the article topic. If the article is about selling a home, use an image of a home with a for sale sign or a family making a selling decision — NOT a generic advisor image that doesn't match the article context.
- Apply overlay: `(8) Rule - AskRoss.ca - For The Closer - No Overlay - Just Logo.png` (logo only, no scrim)
- **NO TEXT rendered — ever. Logo only.**

**FAQ H2 variant:**
- **ALWAYS** pick one of the two fixed pool images — never generate with Gemini, never fetch from Pexels:
  - `Reusable Image Large Article Image Assets/AskRoss.ca - All of the FAQs in this article.png`
  - `Reusable Image Large Article Image Assets/AskRoss.ca - All of the FAQs in this article (2).png`
- **NO overlay applied** — pool images are the complete deliverable. Just resize to 1920×1080 and save.
- **NO TEXT rendered — ever.**

---

### 2. Feature Image — 700×450  ✅ LOCKED IN 2026-05-20

**Compositing steps:**
1. Resize/center-crop background image to 700×450
2. Save as `{title} - Feature Background RAW.png` (NO overlay — reusable asset)
3. Fit title text first → actual line count drives overlay selection automatically
4. Apply overlay (auto-selected: 2-line or 3-line)
5. Render Layer 1 (THEME), then Layer 2 (TITLE)

**Overlay selection (automatic — never use manifest title_line_count):**
- Fit title → actual lines ≤ 2 → 2-line overlay
- Fit title → actual lines = 3 → 3-line overlay
- Height budget enforced: font auto-reduces so text never overflows bottom red bar

**Layer 1 — THEME (topic label):**
- Font: **Aleo Bold** (`fonts/Aleo/static/Aleo-Bold.ttf`)
- Size: **13px** (auto-fits down if label too long)
- Case: **ALL CAPS**
- Letter spacing: **1px**
- Position: x=138, y=280
- Max width: 560px
- Content: set via `manifest["theme_label"]` (e.g. "Housing News"). Fallback keyword categories: Mortgage Rates, Renewal Tips, Refinancing, Buyer's Guide, Financial Advice, Market Update, Housing News.

**Layer 2 — MAIN TITLE:**
- Font: **Open Sans Bold 700** (`fonts/Open_Sans/static/OpenSans-Bold.ttf`)
- Case: **ALL CAPS**
- Letter spacing: **0px**
- Size: **20px start** (auto-fits down for both width AND height budget)
- Line height: **1.3× font size**
- Position: x=138, y=299 (dynamic: THEME_Y + theme_font.size + 6px gap)
- Max width: **440px**
- Max lines: 3

**Typography rules (never break):**
- Top line must be longer than the second line
- No single word on the last line (widow prevention enforced in code)

**Height budget zones:**
- 2-line overlay: text zone bottom = y≈360
- 3-line overlay: text zone bottom = y≈390

---

### 3. Desktop Banner — 1286×300

**Compositing steps:**
1. Resize/center-crop the Feature Background RAW to 1286×300
2. Apply overlay: `Banner - Title of Article - Overlay.png`
3. **NO TEXT rendered — ever.**

The banner overlay is a pure uniform scrim with no embedded design elements (confirmed by pixel inspection: no alpha variation). The banner communicates through the photograph alone.

**Crop math for 1920×1080 source:**
- Scale to fit width: `new_w=1286, new_h=723`
- Default center crop: `top=211` (rows 211–511 of 723)
- Valid range: `top=0` (very top) to `top=423` (very bottom)

**For sign-based images (selling articles), find the sign before cropping:**
```python
import numpy as np
arr = np.array(bg)
# FOR SALE signs are red: R>150, G<80, B<80
red_mask = (arr[:,:,0] > 150) & (arr[:,:,1] < 80) & (arr[:,:,2] < 80)
red_per_row = red_mask.sum(axis=1)
sign_center_original = int(np.median(np.argsort(red_per_row)[-20:]))
scale = 723 / bg.height
sign_center_scaled = int(sign_center_original * scale)
top = max(0, min(sign_center_scaled - 150, 423))
```
- For Pool 1 (`home for sale.png`): sign detected at scaled y≈339, top=189 from detection, then +50px nudge → **top=239** was the approved final value

---

### 4. Mobile Banner — 400×600

**Compositing steps:**
1. Resize/center-crop the Feature Background RAW to 400×600
2. Apply overlay: `MOBILE - Title of Article - Overlay.png`
3. **NO TEXT rendered — ever.**

**Crop math for 1920×1080 source:**
- Scale to fit height: `new_h=600, new_w=1067`
- Default center crop: `left=333` (columns 333–733 of 1067)
- Valid range: `left=0` (far left) to `left=667` (far right)

**For sign-based images:** The portrait crop (400px wide from 1067px) will cut off the sign if it's off-center horizontally. Adjust `left` to frame the sign:
- Start at `left=667` (far right) and nudge left until sign is in frame
- For Pool 1: `left=566` (100px left of far right) was the approved final value

---

### 5. GMB Share Images — 1200×900 × 4 cities  ✅ LOCKED IN 2026-05-20

**The overlay IS the branding.** Each city overlay has embedded logo, brand text, red bars, and city name pre-rendered. The overlay must be semi-transparent so real photo backgrounds show through.

**Compositing steps:**
1. Resize/center-crop the Feature Background RAW to 1200×900
2. Apply city overlay (alpha_composite — semi-transparent)
3. Render ARTICLE TITLE text in the title zone

**Title text rendering — LOCKED VALUES:**
- Font: **Open Sans Bold 700** (`fonts/Open_Sans/static/OpenSans-Bold.ttf`)
- Case: **ALL CAPS**
- Size: **35px start** (auto-fits down to min 18px if title too long)
- Letter spacing: **1px** between each character (rendered char-by-char)
- Line height: **1.3× font size** (=45px at 35px)
- Position: x=236, y=573
- Max width: **850px**
- Max lines: **2**
- Drop shadow: offset 1px, GaussianBlur radius 3, opacity 114/255

**Typography rules (never break):**
- Top line must be longer than the second line
- No single word on the last line (widow prevention enforced in code)

**Cities:** Toronto, Ottawa, Richmond Hill, Mississauga (set via `manifest["gmb_locations"]`)

---

## Shared compositing rules (apply to all image types)

### Resize & center-crop
```python
def resize_and_center_crop(img, target_w, target_h):
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:          # wider than target → scale by height
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:                                  # taller than target → scale by width
        new_w = target_w
        new_h = int(new_w / src_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))
```

### Overlay application
```python
overlay = Image.open(overlay_path).convert("RGBA")
if overlay.size != (target_w, target_h):
    overlay = overlay.resize((target_w, target_h), Image.LANCZOS)
result = Image.alpha_composite(background.convert("RGBA"), overlay)
```

### Drop shadow (for all text rendering)
```python
SHADOW_OFFSET  = 1     # 1px right + 1px down
SHADOW_BLUR    = 3     # GaussianBlur radius 3 (= Photoshop Size 6px)
SHADOW_OPACITY = 114   # 45% of 255
# Technique: draw black text on transparent layer → GaussianBlur → composite → draw white text
```

### Save as RGB
```python
def save_rgb(img, path):
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (0, 0, 0))
        bg.paste(img, mask=img.split()[3])
        img = bg
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path, "PNG", optimize=True)
```

---

## Output folder structure (exact — never deviate)

```
out/Blog Images - {article_title}/
├── Feature Image - {article_title}.png              700×450
├── {article_title} - Feature Background RAW.png     700×450  ← no overlay
├── Banner - {article_title}.png                     1286×300
├── Mobile - {article_title}.png                     400×600
├── BLOG POST - Large Article Images for Askross.ca/
│   ├── AskRoss.ca - {H2 text sanitized}.png        1920×1080  ← one per H2
│   └── ...
└── BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/
    ├── Toronto - {article_title}.png                1200×900
    ├── Ottawa - {article_title}.png                 1200×900
    ├── Richmond Hill - {article_title}.png          1200×900
    └── Mississauga - {article_title}.png            1200×900
```

---

## Filename sanitization

Pattern for article images: `AskRoss.ca - {n} - {sanitized_h2_text}.png`

Where `{n}` is the 1-based sequential position of the H2 in the article (as they appear top-to-bottom, matching the article's jump-to-section order).

Sanitize H2 text:
- Remove trailing `?` and `!`
- Replace `: ` with `_ ` (colon-space → underscore-space)
- Replace `:` with `_` (bare colon → underscore)  
- Remove `"`, `*`, `\`, `/`, `<`, `>`, `|`
- Strip leading/trailing whitespace
- Preserve apostrophes

Examples:
- `AskRoss.ca - 1 - What is actually happening to Canadian homeowners right now.png`
- `AskRoss.ca - 8 - Advice from Ross Taylor Mortgages_ Knowing when it's time to sell your home.png`
- `AskRoss.ca - 9 - List of all FAQs_ Canadian homeowners who can't afford their renewal or refinance.png`

---

## JPEG conversion — final step for every deliverable (locked in 2026-05-22)

**All composited outputs are saved as PNG during pipeline execution.** After the final selection folder is confirmed, convert the entire folder to JPEG as the last standardization step.

**Rule:** PNG = working/archival format. JPEG = delivery format. Both are kept.

**Standard quality:** 95 (visually lossless at web display sizes, significantly smaller files than PNG).

**Implementation — call once after final selection is ready:**
```python
from src.compositors.shared import convert_folder_to_jpeg

convert_folder_to_jpeg(
    src_dir="out/final selection",
    dst_dir="out/final selection - JPEG",
    quality=95,
)
```

**Output folder naming convention:** `{folder name} - JPEG/` alongside the PNG folder. Mirrors the exact same subfolder structure (including GMB subfolder).

**Applies to all image types:**
| Image type | PNG kept | JPEG copy |
|---|---|---|
| Large Article Images (1920×1080) | ✓ | ✓ |
| Feature Image (700×450) | ✓ | ✓ |
| Desktop Banner (1286×300) | ✓ | ✓ |
| Mobile Banner (400×600) | ✓ | ✓ |
| GMB Share Images (1200×900) | ✓ | ✓ |

---

## What NEVER gets text rendered on it

| Image type | Text? | Reason |
|---|---|---|
| Desktop banner (1286×300) | ❌ NEVER | Photo-only intentional design |
| Mobile banner (400×600) | ❌ NEVER | Photo-only intentional design |
| Bottom-line (1920×1080) | ❌ NEVER | Logo-only closer, no text |
| FAQ image (1920×1080) | ❌ NEVER | Fixed pool image, no overlay, no text — copy + rename only |
| Feature Background RAW | ❌ NEVER | This is the clean reusable background |

---

## Phase 1 test backgrounds

Use these solid colors for Phase 1 testing (no API calls):
- Article images / bottom-line / FAQ: `Image.new("RGB", (1920, 1080), (80, 90, 100))`
- Feature / banner / GMB backgrounds: `Image.new("RGB", (1920, 1080), (70, 80, 95))`

The solid color must be dark enough that white text is visible. Use a neutral dark blue-gray.

---

## Image generation rules — learned from testing (2026-05-21)

### Scene mode selection (for Gemini / AI generation)
Pick ONE mode per section. Reference: `prompt-builder.md`.
- **OBJECT mode** — most reliable. Use for: equity, renewals, credit score, waiting/time, financial reset (object/still-life in frame, no people). Concept reads clearly, no overdramatic faces.
- **PEOPLE mode** — use when human story matters. Rules: subjects must look at each other or at documents — NEVER head-on into the camera lens. Medium shot with both heads fully in frame. Not movie-poster dramatic.
- **PLACE mode** — use for institutional or location-driven topics. Building/house as hero.

### What works
- Object still-life prompts (house model + piggy bank, hourglass on calendar, renewal letter) — clear, uncluttered, concept reads at a glance
- Canadian home exterior when article is about selling — contextually obvious, no over-dramatization
- Couples looking at documents/tablets (NOT at camera) — natural, warm, editorial feel

### What never works
- Person staring directly at the camera — always looks overdramatic and AI-generated
- Readable text or signage baked into the AI-generated image — violates brand and looks unpolished
- Autumn/fall foliage when article publishes in spring or summer — always check current season
- Compound Pexels search strings (4+ descriptors) — return irrelevant or mixed results; use 3–4 words max

### Prompt structure (Gemini)
Every prompt must specify:
1. Scene mode (OBJECT / PEOPLE / PLACE)
2. Subject framing: "focal point on the upper-third horizontal line, occupying 35–55% of frame height"
3. Upper-left quiet zone: "upper-left ~260×100px region must be clear — sky, blurred foliage, or plain wall"
4. Current season foliage — never use autumn unless article publishes Sept–Nov
5. No text/logos/watermarks in generated image
6. Avoidance tail: cropped heads, face staring at camera, excessive sky, fall foliage, plastic skin, distorted hands, 3D render style

### Selling articles — feature/banner/GMB/bottom-line background
- **Never fetch from Pexels** — stock "for sale" images don't match brand
- **Always use prebuilt pool:** `references/BLOG POST - Large Article Images for Askross.ca/Reusable Image Large Article Image Assets/home for sale options/` (8 options)
- Pick randomly from pool. Applies to feature image, desktop banner, mobile banner, all GMB cities, and bottom-line

**Pool image selection guide (learned 2026-05-21):**
| File | Description | Best for |
|---|---|---|
| `home for sale.png` | FOR SALE sign as hero, large/prominent, house blurred, spring foliage, no family | Feature, banner, GMB — sign is always in frame |
| `home for sale (2).png` | FOR SALE sign right side, wooded background, no family | Banner alternative |
| `home for sale (3).png` | Family from behind, sign on edge | **AVOID for banner** — sign gets cut off in 1286×300 crop |
| `home for sale (4).png` | FOR SALE sign + house, overcast sky, no family | Acceptable |
| `home for sale (5).png` | Wooden blocks spelling SALE + house model | Conceptual only |
| `home for sale (6).png` | Family celebrating, SOLD + sign | Editorial/emotional |
| `home for sale (7).png` | FOR SALE sign + house both prominent, no family, blue sky | Feature, banner, GMB — good clean alternative |
| `home for sale (8).png` | FOR SALE sign + house, no family | Acceptable |

**Recommended defaults:** Pool 1 (`home for sale.png`) or Pool 7 (`home for sale (7).png`) for any format where the sign must be clearly visible.

### Pexels search term rules
- 3–4 words maximum
- Match the core object or scene, not a description of mood
- Good: `hourglass calendar time`, `mortgage renewal letter`, `credit score laptop`
- Bad: `calendar waiting financial uncertainty home`, `credit score financial improvement laptop`

---

## Phase 2 image generation

Uses Google Gemini 2.5 Flash Image via OpenRouter:
```python
response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "google/gemini-2.5-flash-image",
        "messages": [{"role": "user", "content": prompt}],
    },
    timeout=120,
)
```

API key: `OPENROUTER_IMAGE_API_KEY` from `.env` in working directory root.

**`.env` location:** The `.env` is NOT in the working directory root — it lives at:
```
references/(2) Newsletter Image Creation - Use for process creation reference/.env
```
The `_load_env()` function in `generate_gemini.py` handles this fallback automatically. Always call `_load_env()` (not bare `load_dotenv`) in any script that needs API keys.

Generate 2 candidates per section in Phase 2. Present both. User picks best.

---

## Full session workflow (locked in 2026-05-21)

This is the complete end-to-end process for creating blog article images for one article.

### Step 1 — Prepare manifest
Create `out/manifest.json`:
```json
{
  "title": "Article Title Here",
  "slug": "article-title-here",
  "title_line_count": 2,
  "theme_label": "Housing News",
  "gmb_locations": ["Toronto", "Ottawa", "Richmond Hill", "Mississauga"],
  "h2_sections": [
    {
      "text": "H2 section title",
      "section_number": 2,
      "filename": "AskRoss.ca - 1 - H2 section title.png",
      "is_bottom_line": false,
      "is_faq": false,
      "prompt_hint": "Visual description for image generation"
    }
  ]
}
```
- `section_number` = the heading number in the article (H1=1, first H2=2, etc.)
- `filename` uses sequential 1-based index: `AskRoss.ca - 1 - ...`, `AskRoss.ca - 2 - ...`
- Last regular section before FAQ is always `is_bottom_line: true`
- FAQ section is always `is_faq: true`

### Step 2 — Generate backgrounds
**For selling articles** ("sell", "selling", "for sale" in title):
- Feature/banner/GMB/bottom-line backgrounds → use home for sale pool (Pool 1 or Pool 7 recommended)
- Article section backgrounds → run Pexels or Gemini as normal

**For all other articles:**
```bash
python generate_gemini.py   # AI generation via Gemini 2.5 Flash
# OR
python generate_phase2.py   # Pexels stock photos
```
Raw backgrounds saved to `out/generated/`.

### Step 3 — Review outputs
In the output folder (`out/Blog Images - .../BLOG POST - Large Article Images.../`):
- Create three subfolders: `good/`, `close but not/`, `no/`
- Sort each image into the right folder by visual inspection
- Criteria for **good**: correct subject matter, 2-line title fits well, no AI artifacts, background suits the section topic
- Criteria for **close but not**: right concept but wrong framing, title wraps to 3 lines, sign cut off
- Criteria for **no**: wrong subject entirely, overdramatic, wrong season, face staring at camera

### Step 4 — Compile BEST folder
Create `out/BEST - {article_title}/` and recomposite the selected backgrounds:
```python
# Apply alternating positions (0-indexed regular sections):
positions = ["lower-left", "center", "lower-left", "center", ...]
for i, section in enumerate(regular_sections):
    compose_article_image(
        h2_text=section["text"],
        background=Image.open(chosen_bg),
        overlay_path=article_overlay,
        font_path=font_archivo,
        out_path=out_path,
        force_position=positions[i],
    )
```
- Bottom-line: apply bottom-line overlay (no text)
- FAQ: copy from pool, resize, no overlay, no text

### Step 5 — Fine-tune
Review BEST folder and apply targeted fixes:
- Title position wrong → recomposite with different `force_position`
- Title Y off → recomposite with `text_y + 5` (common for center position)
- Background wrong → regenerate just that section
- Alternative needed → generate ALT file (keep original, add ALT suffix to filename)

### Step 6 — Feature, Banner, GMB
**For selling articles:** Use Pool 1 or Pool 7 as background.
```python
# Banner crop — use red pixel detection for Pool 1/7:
# (see Banner section above for full code snippet)
# Pool 1 approved values: banner top=239, mobile left=566

compose_feature_image(title, theme_label, background=pool_bg, ...)
compose_all_banners(background=pool_bg, ...)
compose_all_gmb_images(title, background=pool_bg, ...)
```

### Step 7 — Final selection
Create `out/final selection/` and populate:
```
final selection/
├── Feature Image - {title}.png                      700×450
├── Banner - {title}.png                             1286×300
├── Mobile - {title}.png                             400×600
├── AskRoss.ca - 1 - {h2}.png                        1920×1080
├── AskRoss.ca - 2 - {h2}.png
├── ... (all regular sections)
├── AskRoss.ca - N - Advice from Ross Taylor Mortgages_ ...  (bottom-line)
├── AskRoss.ca - N+1 - List of all FAQs_ ...         (FAQ)
├── AskRoss.ca - X ALT WARNING - {h2}.png            (any approved alternates)
└── BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/
    ├── Toronto - {title}.png                        1200×900
    ├── Ottawa - {title}.png
    ├── Richmond Hill - {title}.png
    └── Mississauga - {title}.png
```

### Step 9 — Convert final selection to JPEG
```python
from src.compositors.shared import convert_folder_to_jpeg
convert_folder_to_jpeg("out/final selection", "out/final selection - JPEG", quality=95)
```
This is always the last step. PNG folder = archival. JPEG folder = delivery to client / upload.

### Step 8 — Archive and clean up
```
out/
├── final selection/         ← deliverable
├── generated/               ← keep (raw backgrounds, reusable)
├── manifest.json            ← keep
└── _archive/                ← move everything else here
    ├── Blog Images - {title}/
    ├── Blog Images - AI Generated - {title}/
    ├── BEST - {title}/
    └── test-output/
```
