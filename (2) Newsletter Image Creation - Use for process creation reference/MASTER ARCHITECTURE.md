# Newsletter Image Creation — Master Architecture

**Root folder:** `Newsletter Image Creation/`
**Last updated:** 2026-04-29

---

## Folder structure

```
Newsletter Image Creation/
├── .env                          ← shared API keys (all scripts read from here)
├── requirements.txt              ← Python dependencies
├── out/                          ← ALL output images (shared across all workflows)
├── in/                           ← Custom input images (for --source custom / --banner-image)
├── MASTER ARCHITECTURE.md        ← this file
├── WORKFLOW.md                   ← full visual flowchart + step-by-step process
│
├── (1) Banner Images/
│   ├── build_newsletter_banner.py         ← banner script
│   ├── ask-ross-newsletter-banner-spec.md ← banner rules + spec
│   ├── overlays/
│   │   └── Logo + Grey Transparent Layer - Banner.png
│   ├── fonts/
│   │   └── Archivo_Black/ArchivoBlack-Regular.ttf
│   └── samples/                           ← reference sample banners
│
├── (3) Section Images/
│   ├── build_newsletter_section.py        ← section script
│   ├── ask-ross-newsletter-section-spec.md← section rules + spec
│   └── overlays/
│       ├── CMT logo.png
│       └── AskRoss Logo + Grey Transparent Layer.png
│
├── (2) GMB Share Images/
│   ├── build_newsletter.py                ← AI source
│   ├── build_newsletter_sonar.py          ← Sonar source
│   ├── build_newsletter_custom.py         ← Custom source
│   ├── build_newsletter_pexels.py         ← Pexels source
│   ├── ask-ross-newsletter-agent-spec.md
│   ├── ask-ross-newsletter-sonar-spec.md
│   ├── ask-ross-newsletter-custom-image-spec.md
│   ├── ask-ross-newsletter-pexels-spec.md
│   ├── overlays/
│   │   └── ask-ross-overlay.png
│   └── fonts/
│       ├── Aleo-Regular.ttf
│       ├── Aleo-Bold.ttf
│       └── OpenSans-Regular.ttf
│
└── Archive/
    ├── old-overlays/              ← gradient overlay (replaced by grey scrim)
    ├── open-sans/                 ← full font package (only Regular is used)
    ├── aleo/                      ← full font package (TTF copies in fonts/ are used)
    └── prompt-builder.md          ← superseded by spec files
```

---

## API keys (all in `.env`)

| Key | Used by | Service |
|---|---|---|
| `OPENROUTER_IMAGE_API_KEY` | Banner AI, Section AI, GMB AI | OpenRouter → Gemini 2.5 Flash Image |
| `PERPLEXITY_API_KEY` | Banner Sonar, GMB Sonar | Perplexity Sonar |
| `PEXELS_API_KEY` | Banner Pexels, Section Pexels, GMB Pexels | Pexels API |

---

## Three image types

### 1 — Banner Image (`(1) Banner Images/`)

**Canvas:** 1200 × 800 px
**Output:** `out/{name} Banner Raw.png` + `out/{name} Banner.png`
**Script:** `(1) Banner Images/build_newsletter_banner.py`
**Spec:** `(1) Banner Images/ask-ross-newsletter-banner-spec.md`

One banner per newsletter issue. Built first, before GMB Share.

**Image source decision:**

| Topic | Source |
|---|---|
| Named politician (Carney, Trump) or major world event | `--source sonar` (1 image, no-text) |
| Everything else | `--source ai` AND `--source pexels` — build both, present for approval |

**Text rule:**

| Subject | Text |
|---|---|
| Ross Taylor | No text |
| Named politician / powerful editorial photo | No text |
| Abstract, scene, lifestyle — no prominent person | Center text |
| People in lower half, space above | Upper-left text (y=213) |
| People in upper half, space below | Lower-left text (y≈550) |

**Typography (locked):**
- Font: Archivo Black, 45px, white `#FFFFFF`
- Line height: 55px
- Left margin: x=193
- Drop shadow: distance 1px, blur radius 3, opacity 114 (45%), black
- Title: SEO question format, sentence case for questions, 40–60 chars (max 80)
- Faces rule: text MUST NEVER overlap a face

---

### 2 — GMB Share Image (`(2) GMB Share Images/`)

**Canvas:** 1200 × 900 px (banner 1200×638 + white info band 1200×262)
**Output:** `out/{title1} GMB Share.png`
**Scripts:** 4 scripts (one per source)
**Specs:** 4 spec files (one per source)

Built AFTER banner is approved, using the approved `Banner Raw.png` as input.

**Standard command (using approved banner raw):**
```bash
python "(2) GMB Share Images/build_newsletter_custom.py" \
  --banner-image "out/{name} Banner Raw.png" \
  --title1 "..." --intro "..."
```

**Typography (locked):**
- TITLE1: Aleo Regular, 35px, #1A1A1A, x=230, y=661.72
- TITLE2: Aleo Regular, 35px, #1A1A1A, x=230, y=704.79
- INTRO: OpenSans Regular, 27px, #4A4A4A, x=112, y=761.44, line height 40px
- INTRO: max 245 chars, 3 lines max, line 2 must be longest
- TITLE1: max 55 chars

---

### 3 — (3) Section Images (`(3) Section Images/`)

**Canvas:** 1200 × 400 px
**Output:** `out/{name} Section Raw.png` + `out/{name} Section.png`
**Script:** `(3) Section Images/build_newsletter_section.py`
**Spec:** `(3) Section Images/ask-ross-newsletter-section-spec.md`

One image per newsletter section. No text rendered — image + overlay only.

**Section type and options:**

| Section type | When | Overlay | Build |
|---|---|---|---|
| CMT | Article on canadianmortgagetrends.com | CMT logo (bottom-left) | Article OG image + Pexels (always both) |
| Ask Ross | Ask Ross article, client story, insert | AskRoss grey scrim | AI only (Pexels on request) |

**Faces rule (absolute):** If people appear, faces must never be cut off.
- Portrait source → top-anchored crop
- Landscape source → center crop

---

## Running scripts

All scripts use `SCRIPT_DIR.parent` (`Newsletter Image Creation/`) for `.env`, `out/`, and `in/`.

```bash
# Run from anywhere — use full relative or absolute path to script
python "G:/Shared drives/.../Newsletter Image Creation/(1) Banner Images/build_newsletter_banner.py" --source ai ...

# Or cd to the root folder:
cd "G:/Shared drives/.../Newsletter Image Creation"
python "(1) Banner Images/build_newsletter_banner.py" --source ai ...
python "(3) Section Images/build_newsletter_section.py" --source cmt ...
python "(2) GMB Share Images/build_newsletter_custom.py" --banner-image "out/{folder}/..." ...
```

Use `--output-dir "out/{folder}"` on every script call to route all output into the issue folder (see workflow below).

---

## Output naming conventions

All output for a newsletter issue lives in a dedicated subfolder: `out/{issue-folder}/`

**Issue folder naming:** short slug derived from the newsletter title, e.g. `Selling at Renewal`, `Spring 2025 Market`, `Carney Housing Win`.

| Image type | Path pattern |
|---|---|
| Banner Raw | `out/{issue-folder}/{name} Banner Raw.png` |
| Banner Final | `out/{issue-folder}/{name} Banner.png` |
| Banner Credits | `out/{issue-folder}/{name} Banner Credits.txt` |
| GMB Share | `out/{issue-folder}/{title1} GMB Share.png` |
| GMB Credits | `out/{issue-folder}/{title1} Credits.txt` |
| Section Raw | `out/{issue-folder}/{name} Section Raw.png` |
| Section Final | `out/{issue-folder}/{name} Section.png` |
| Section Credits | `out/{issue-folder}/{name} Section Credits.txt` |

Pass `--output-dir "out/{issue-folder}"` to every script call. The folder must exist before running — create it manually or with `mkdir`.

---

## Cache files (in `out/`)

| File | Used by |
|---|---|
| `_banner_sonar_cache.json` | Banner Sonar — stores candidate list from `--list-images` |
| `_sonar_candidates_cache.json` | GMB Sonar — same purpose |

---

## Full issue workflow (in order)

```
1. Receive complete newsletter text

2. CREATE ISSUE FOLDER
   → Derive a short slug from the newsletter title (e.g. "Selling at Renewal")
   → mkdir "out/{issue-folder}"
   → All subsequent script calls use --output-dir "out/{issue-folder}"

3. BUILD BANNER
   → Sonar (politician/world event) or AI + Pexels (everything else)
   → python "(1) Banner Images/build_newsletter_banner.py" ... --output-dir "out/{issue-folder}"
   → Present for approval
   → Revise title, regenerate image, or pick different Sonar candidate as needed
   → APPROVED → lock Banner Raw

4. BUILD GMB SHARE (using approved Banner Raw)
   → python "(2) GMB Share Images/build_newsletter_custom.py" --banner-image "out/{issue-folder}/{name} Banner Raw.png" ... --output-dir "out/{issue-folder}"
   → Present title1 + intro for approval
   → Revise text if needed
   → APPROVED → lock GMB Share

5. BUILD SECTION IMAGES (one per section)
   → CMT section: build article OG image + Pexels — both with --output-dir "out/{issue-folder}"
   → Ask Ross section: build AI only — with --output-dir "out/{issue-folder}"
   → Present all sections for approval
   → Revise or regenerate as directed
   → APPROVED → keep approved files
   → REJECTED → delete rejected asset files

6. DONE — all approved images in out/{issue-folder}/, ready for newsletter
```
