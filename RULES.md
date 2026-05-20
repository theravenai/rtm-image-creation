# Blog Article Image Creation — Rules (Never Break These)

**Ground truth reference:** `references/(1) Complete Blog Article Images Sample/`
**SOP reference:** `SOP_ Create Blog Article Images and Social Share Assets.pdf`
**Newsletter reference:** `references/(2) Newsletter Image Creation - Use for process creation reference/`

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
| Aleo SemiBold | `fonts/Aleo/static/Aleo-SemiBold.ttf` | Feature image THEME text |
| Open Sans ExtraBold | `fonts/Open_Sans/static/OpenSans-ExtraBold.ttf` | Feature image TITLE text (ALL CAPS) |
| Archivo Black | `references/(2) Newsletter Image Creation - Use for process creation reference/(1) Banner Images/fonts/Archivo_Black/ArchivoBlack-Regular.ttf` | Large article images |

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
TEXT_MAX_WIDTH_LEFT   = 1400   # left-aligned positions (upper-left, lower-left)
TEXT_MAX_WIDTH_CENTER = 1500   # center position
UPPER_LEFT_Y          = 284    # y=213 in newsletter × 1080/800 = 288 → 284
LOWER_LEFT_BOTTOM_PAD = 189    # 140 × 1080/800 — text_y≈700 for 2 lines
```

**Auto text position (luminance analysis — same as newsletter):**
- Measure average luminance in 3 zones: upper-left, lower-left, center
- Pick the darkest zone → best contrast for white text
- Faces rule: text must NEVER overlap a face

**Bottom-line H2 variant:**
- Background: random pick from `Reusable Image Large Article Image Assets/AskRoss.ca - Bottom line or Advice from Ross Taylor Mortgages*.png`
- Apply overlay: `(8) Rule - AskRoss.ca - For The Closer - No Overlay - Just Logo.png` (logo only, no scrim)
- **NO TEXT rendered — ever. Logo only.**

**FAQ H2 variant:**
- Background: random pick from `Reusable Image Large Article Image Assets/AskRoss.ca - All of the FAQs in this article*.png`
- Apply overlay: `(1) AskRoss.ca - Just logo and grey overlay.png` (standard)
- **Render H2 title text** (same typography as regular article images)

---

### 2. Feature Image — 700×450

**Compositing steps:**
1. Resize/center-crop background image to 700×450
2. Save as `{title} - Feature Background RAW.png` (NO overlay — this is the reusable asset)
3. Apply overlay (2-line or 3-line depending on `title_line_count`)
4. Render TWO text layers

**Overlay selection:**
- `title_line_count == 2` → use `Feature image - Use this is title is two lines - overlay.png`
- `title_line_count >= 3` → use `Feature image - use this if title is three lines - overlay.png`

**The overlay provides:** uniform 39% dark scrim + AskRoss.ca logo circle at x≈138–160, y=229–239, and red accent bar at y≈261–264

**TWO text layers (rendered after overlay):**

**Layer 1 — THEME (topic label):**
- Font: **Aleo SemiBold** (`fonts/Aleo/static/Aleo-SemiBold.ttf`)
- Size: **~16px** (auto-fit to max 2 words / short label)
- Color: white #FFFFFF
- Position: left-aligned at **x=138, y=276** (just below the logo/red-bar design element)
- Max width: 560px
- Content: a short 2–4 word topic label derived from the article (e.g. "Mortgage Rates", "Bank of Canada", "Home Equity", "Selling Your Home")

**Layer 2 — MAIN TITLE:**
- Font: **Open Sans ExtraBold** (`fonts/Open_Sans/static/OpenSans-ExtraBold.ttf`)
- Case: **ALL CAPS** (`.upper()`)
- Size: **~22px** (auto-fit: try sizes 28→14 until text fits in max_width)
- Color: white #FFFFFF
- Position: left-aligned at **x=138, y=306** (for 2-line overlay)
- Max width: 560px
- Line height: size + 10px
- For 3-line overlay: y=286 (10px higher to accommodate extra line)

**Title line count logic:**
Measure how many lines the MAIN TITLE wraps to at max_width=560px and the chosen font size. If ≤2 lines → use 2-line overlay. If 3 lines → use 3-line overlay. Never allow 4+ lines — reduce font size until it fits in 3 lines.

---

### 3. Desktop Banner — 1286×300

**Compositing steps:**
1. Resize/center-crop the Feature Background RAW to 1286×300
2. Apply overlay: `Banner - Title of Article - Overlay.png`
3. **NO TEXT rendered — ever.**

The banner overlay is a pure uniform scrim with no embedded design elements (confirmed by pixel inspection: no alpha variation). The banner communicates through the photograph alone.

---

### 4. Mobile Banner — 400×600

**Compositing steps:**
1. Resize/center-crop the Feature Background RAW to 400×600
2. Apply overlay: `MOBILE - Title of Article - Overlay.png`
3. **NO TEXT rendered — ever.**

Same rule as desktop banner. The mobile crop + overlay is the complete deliverable.

---

### 5. GMB Share Images — 1200×900 × 4 cities

**The overlay IS the branding.** Each city overlay (Toronto, Ottawa, Richmond Hill, Mississauga) has embedded at approximately y=456–686:
- AskRoss.ca logo (y≈456–476, x≈236–276)
- "AskRoss.ca" brand text (y≈482–494, x≈236–380)
- Red accent bar (y≈512–518, x≈237–386, RGB #E00B1A)
- City name, pre-rendered per city (y≈544–558, x≈236–422) — this is what differs between city overlays
- Second red accent bar (y≈680–686)

**Compositing steps:**
1. Resize/center-crop the Feature Background RAW to 1200×900
2. Apply city overlay (alpha_composite)
3. Render ARTICLE TITLE text in the title zone

**Title text rendering:**
- Font: **Archivo Black** (same as article images)
- Size: **28px** (auto-fit to max width — try from 34 down to 18)
- Color: white #FFFFFF
- Position: left-aligned at **x=237, y=587**
- Max width: **960px** (1200 - 237 - 3px right margin)
- Line height: 40px
- Drop shadow: same as article images (offset 1, blur 3, opacity 114)
- Wraps to 2 lines if needed (line 2 at y=587+40=627)
- This is the H1 ARTICLE TITLE (not an H2), rendered identically across all 4 cities

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

Pattern for article images: `AskRoss.ca - {sanitized_h2_text}.png`

Sanitize H2 text:
- Remove trailing `?` and `!`
- Replace `: ` with `_ ` (colon-space → underscore-space)
- Replace `:` with `_` (bare colon → underscore)  
- Remove `"`, `*`, `\`, `/`, `<`, `>`, `|`
- Strip leading/trailing whitespace
- Preserve apostrophes

---

## What NEVER gets text rendered on it

| Image type | Text? | Reason |
|---|---|---|
| Desktop banner (1286×300) | ❌ NEVER | Photo-only intentional design |
| Mobile banner (400×600) | ❌ NEVER | Photo-only intentional design |
| Bottom-line (1920×1080) | ❌ NEVER | Logo-only closer, no text |
| Feature Background RAW | ❌ NEVER | This is the clean reusable background |

---

## Phase 1 test backgrounds

Use these solid colors for Phase 1 testing (no API calls):
- Article images / bottom-line / FAQ: `Image.new("RGB", (1920, 1080), (80, 90, 100))`
- Feature / banner / GMB backgrounds: `Image.new("RGB", (1920, 1080), (70, 80, 95))`

The solid color must be dark enough that white text is visible. Use a neutral dark blue-gray.

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

Generate 2 candidates per section in Phase 2. Present both. User picks best.
