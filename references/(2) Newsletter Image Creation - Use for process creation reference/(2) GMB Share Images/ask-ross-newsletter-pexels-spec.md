# Ask Ross Newsletter — Pexels Stock Image Spec

**For:** Raven AI agent (Claude Code) — monthly workflow for news/editorial newsletter images
**Output:** Two PNGs in `out/` — 1200 × 900 GMB Share and 1200 × 638 Banner
**Script:** `build_newsletter_pexels.py`
**When to use:** Any issue where a real photograph is more appropriate than AI-generated art — news events, real public figures, real institutions, political or economic stories

---

## When to use this workflow vs. the AI workflow

| Use Pexels (`build_newsletter_pexels.py`) | Use AI (`build_newsletter.py`) |
|---|---|
| Real public figures (Trump, Trudeau, BoC Governor) | Lifestyle scenes with fictional people |
| Real institutions (Bank of Canada, Parliament Hill) | Generic Canadian neighborhoods |
| News events (trade war, tariffs, rate announcement) | Abstract/aspirational themes |
| Editorial or political content | Seasonal or emotional storytelling |
| Any topic where "a real photo" is the right call | Any topic where setting/mood is the story |

---

## Step 1 — Build the Pexels search query

Read the newsletter and identify the single most visual, searchable element:

### Query rules

| Topic type | Query strategy | Examples |
|---|---|---|
| Real person | Full name + topic keyword | `Donald Trump tariffs`, `Justin Trudeau housing` |
| Real institution | Institution name | `Bank of Canada`, `Parliament Hill Ottawa` |
| Economic event | Plain descriptive terms | `US Canada trade war`, `mortgage rates Canada` |
| Real estate topic | Specific and Canadian | `Toronto condo market`, `Canadian housing market` |
| Financial abstract | Keep concrete | `stock market decline`, `interest rate cut` |

**Rules:**
- 2–4 words maximum
- Prefer specific over generic: `Donald Trump tariffs` > `trade policy`
- Always use landscape orientation (handled automatically by the script)
- If the first result isn't ideal, use `--list-photos` to browse and `--photo-index N` to pick

### Browsing photos before building

Always run `--list-photos` first when the topic involves a real person or specific event:

```bash
python build_newsletter_pexels.py --list-photos --pexels-query "Donald Trump tariffs"
```

This prints the top 15 results with photographer credits and Pexels URLs. Pick the index of the best photo, then pass it via `--photo-index`.

---

## Step 2 — Prepare the text fields

Extract from the newsletter:

| Field | Rule | Max chars |
|---|---|---|
| `title1` | Lead article headline or issue title | **55 characters** |
| `title2` | Always `\| Ask Ross Newsletter` — never change | n/a |
| `intro` | 2–3 sentence summary of the issue's key topics. No em dashes. | **245 characters** |

**Title1 examples:**
- `"How the US Trade War Is Hitting Canada's Housing"` (48 chars) ✓
- `"Bank of Canada Cuts Rates Again: What It Means"` (47 chars) ✓

**Intro rules:**
- Maximum 245 characters
- No em dashes (`—`) or en dashes (`–`) — use ` - ` instead
- Hard-capped at 3 lines regardless of character count
- Line 2 must be the longest line — script auto-balances (short / long / short shape)
- Line 3 minimum 3 words — script auto-enforces; line 3 can have more than 3 words

---

## Step 3 — Run the build script

```bash
# 1. Browse available photos
python build_newsletter_pexels.py \
  --list-photos \
  --pexels-query "Donald Trump tariffs"

# 2. Build with chosen photo
python build_newsletter_pexels.py \
  --pexels-query "Donald Trump tariffs" \
  --photo-index 0 \
  --title1 "How the US Trade War Is Hitting Canada's Housing" \
  --intro "The US trade war is rattling Canada's economy - lowering rates, cooling the housing market, and squeezing landlords."
```

### Flags

| Flag | Purpose |
|---|---|
| `--pexels-query` | Search query sent to Pexels |
| `--photo-index N` | Pick the Nth result (0 = first/top match) |
| `--photo-count N` | How many results to fetch (default 15, max 80) |
| `--list-photos` | Print available results and exit — use before building |
| `--reuse-banner` | Skip API call, reuse existing Banner PNG. Use for text/layout changes. |
| `--banner-zoom 1.25` | Zoom into lower portion of the banner (1.0 = no zoom) |
| `--title2` | Override only if rebranding. Default: `\| Ask Ross Newsletter` |
| `--output` | Override output path. Default: derived from title1. |

**When to use `--reuse-banner`:** Any time you are only adjusting text content or layout — do NOT call the Pexels API again. Only fetch a new photo when explicitly asked.

---

## Output filenames (auto-derived from title1)

| File | Naming rule |
|---|---|
| GMB Share image | `{title1} GMB Share.png` |
| Banner only | `{title1} Banner.png` |
| Photo credits | `{title1} Credits.txt` |

Colons in title1 become ` - ` for Windows filename compatibility.

---

## Attribution (required by Pexels)

Every build saves a `Credits.txt` file alongside the images:

```
Photo by [Photographer Name]
Photographer: https://www.pexels.com/@photographer
Photo page: https://www.pexels.com/photo/...
Via Pexels: https://www.pexels.com
```

Keep this file. Pexels requires crediting the photographer when using their photos.

---

## Layout constants (locked — same as AI workflow)

Canvas: **1200 × 900 px**, RGB output.

| Element | Top (px) | Left (px) | Max width (px) | Notes |
|---|---|---|---|---|
| BANNER region | 0 | 0 | 1200 × 638 | Stock photo from Pexels |
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

## Pexels API

**Endpoint:** `https://api.pexels.com/v1/search`
**Key variable:** `PEXELS_API_KEY` in `.env`
**Orientation:** Always `landscape`
**Image size used:** `large2x` (~1880px wide — sufficient for 1200px output)

---

## Quality checks (automatic)

1. Output dimensions exactly `(1200, 900)`
2. White band — pixel at `(600, 800)` is `(255, 255, 255)`
3. Banner visible — pixel at `(600, 300)` is not pure black
4. TITLE1 rendered — pixel at `(300, 680)` is not pure white

---

## Monthly variables

| Variable | Changes each issue? |
|---|---|
| Newsletter body (input) | Yes |
| `pexels_query` | Yes |
| `title1` | Yes |
| `intro` | Yes |
| `title2` | No — locked |
| `photo_index` | Sometimes — if first result isn't ideal |
| All layout/font/position constants | No |
| Overlay PNG | No |
