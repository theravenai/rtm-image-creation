# Ask Ross Newsletter — Sonar Image Spec

**For:** Raven AI agent (Claude Code) — finding recent news photos automatically
**Output:** Two PNGs in `out/` — 1200 × 900 GMB Share and 1200 × 638 Banner
**Script:** `build_newsletter_sonar.py`
**When to use:** Newsletter covers a real person or current event and you want a recent photo pulled automatically — no manual image hunting required. Sonar searches the web, finds the most relevant recent articles, and extracts their hero images.

---

## When to use this workflow vs. the others

| Use Sonar (`build_newsletter_sonar.py`) | Use Custom (`build_newsletter_custom.py`) | Use AI (`build_newsletter.py`) |
|---|---|---|
| Real person in the news, no image in hand | You already have a specific image | No image needed — generate one |
| Current events (election, rate decision, policy) | Branded photos, event shots, screenshots | Lifestyle, seasonal, abstract themes |
| Want the freshest available photo automatically | Exact control over the image used | Full creative control |

---

## Step 1 — Build the Sonar search query

Write a short, specific news-style query. Sonar searches the web and returns citations from major outlets; the script extracts the hero image (og:image) from each article page.

### Query rules

| Topic | Query strategy | Example |
|---|---|---|
| Political figure | Full name + recent context | `Mark Carney Canada Prime Minister` |
| Policy event | Person + event | `Mark Carney victory speech election 2025` |
| Economic news | Specific event + year | `Bank of Canada rate cut 2025` |
| General topic | Descriptive + Canadian context | `Canada housing market 2025` |

**Tips:**
- Include the year if you want the most recent results
- Add an action word (speech, press conference, victory) to bias results toward podium/action shots
- Always run `--list-images` first to see what's available before building

### Source priority (built into the search prompt)

Sonar is instructed to prioritise sources in this order:

1. **CNN** (`cnn.com`) — clean 16:9 editorial photography, no baked-in graphics
2. **The New York Times** (`nytimes.com`) — high-quality wire-service photos
3. Reuters, AP, BBC — wire service and broadcast editorial
4. CBC, Globe and Mail, CTV — Canadian editorial

YouTube thumbnails and broadcast show graphics are **automatically skipped**.

### Browse candidates before building

```bash
python build_newsletter_sonar.py \
  --list-images \
  --sonar-query "Mark Carney Liberal minority government"
```

This prints each candidate image with its source article and URL. Pick the index of the best photo, then pass it via `--image-index`.

**What makes a good candidate:**
- Clean editorial shot of the subject speaking, at a podium, or in action — no baked-in text overlays
- Subject clearly identifiable, landscape orientation (wider than tall)
- High resolution (script logs original dimensions)
- Wikipedia Commons images are ideal — freely licensed, clean, professional
- YouTube thumbnails are **automatically skipped** — they always have baked-in graphic text
- Portrait images (taller than wide) are **automatically skipped** in auto mode

**Auto-selection behaviour (no `--image-index` specified):**
The script walks candidates in order and uses the first image that is:
1. Not from YouTube/ytimg.com
2. Landscape oriented (width ≥ height)

If no landscape non-YouTube image is found, it raises an error — use `--list-images` to inspect candidates and pass `--image-index` to force a specific one.

---

## Step 2 — Prepare the text fields

| Field | Rule | Max chars |
|---|---|---|
| `title1` | Lead article headline or issue title | **55 characters** |
| `title2` | Always `\| Ask Ross Newsletter` — never change | n/a |
| `intro` | 2–3 sentence summary. No em dashes. | **245 characters** |

**Intro rules:**
- No em dashes (`—`) or en dashes (`–`) — use ` - ` instead
- Hard-capped at 3 rendered lines regardless of character count
- Line 2 must be the longest line — script auto-balances (short / long / short shape)
- Line 3 minimum 3 words — script auto-enforces; line 3 can have more than 3 words

---

## Step 3 — Run the build script

```bash
# 1. Browse candidates
python build_newsletter_sonar.py \
  --list-images \
  --sonar-query "Mark Carney Liberal minority government"

# 2. Build with chosen image
python build_newsletter_sonar.py \
  --sonar-query "Mark Carney Liberal minority government" \
  --image-index 0 \
  --title1 "Mark Carney's Win: What It Means for Housing" \
  --intro "Canada has a new PM and housing is front and center. From GST breaks for first-time buyers to 4M new homes by 2035, here's what Carney's win means for you."
```

### Flags

| Flag | Purpose |
|---|---|
| `--sonar-query` | Search query sent to Perplexity Sonar |
| `--image-index N` | Which candidate to use (0 = first). Run `--list-images` to browse. |
| `--image-count N` | How many article candidates to search (default 10) |
| `--list-images` | Print candidate images and exit — always run this first |
| `--reuse-banner` | Skip search, reuse cached Banner PNG. Use for text/layout tweaks. |
| `--banner-zoom 1.2` | Zoom into lower portion of banner (1.0 = none) |
| `--title2` | Override only if rebranding. Default: `\| Ask Ross Newsletter` |
| `--output` | Override output path. Default: derived from title1. |

**When to use `--reuse-banner`:** Any time you are only adjusting text — do NOT re-run the Sonar search. Only fetch a new image when using a new query or switching image index.

---

## Output files (auto-derived from title1)

| File | Naming rule |
|---|---|
| GMB Share image | `{title1} GMB Share.png` |
| Banner only | `{title1} Banner.png` |
| Image credits | `{title1} Credits.txt` |

---

## How it works (under the hood)

1. **Sonar search** — Queries Perplexity with your search string; returns a list of citation URLs from major news outlets
2. **OG image extraction** — Fetches each article page and reads the `og:image` meta tag (the article's designated hero photo)
3. **Fallback** — If Sonar's response text contains direct image URLs, those are appended as additional candidates
4. **Download + crop** — Downloads the chosen image and center-crops to 1200×638
5. **Composite + text** — Same overlay and text pipeline as all other workflows

---

## Perplexity API

**Endpoint:** `https://api.perplexity.ai/chat/completions`
**Model:** `sonar`
**Key variable:** `PERPLEXITY_API_KEY` in `.env`

---

## Layout constants (locked — same across all workflows)

Canvas: **1200 × 900 px**, RGB output.

| Element | Top (px) | Left (px) | Max width (px) | Notes |
|---|---|---|---|---|
| BANNER region | 0 | 0 | 1200 × 638 | Photo from Sonar search |
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
