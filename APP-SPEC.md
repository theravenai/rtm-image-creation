# Ask Ross — Blog Image Creation App
## Product Specification & Enhancement Brief

---

## What This Is

A web-based image creation studio built into the Ask Ross app. You paste or submit a blog article, and the app walks you through every step of generating, reviewing, editing, and downloading the complete image package — feature image, article section images, banners, mobile, and GMB — all without touching the command line.

Everything we built in the Python pipeline runs under the hood. This is the front-end wrapper that makes it fast, visual, and repeatable.

---

## Core User Flow

```
Article submitted
       ↓
Manifest auto-generated (H2s extracted, theme assigned, selling flag detected)
       ↓
Backgrounds generated (Gemini AI or Pexels) — streamed to screen as they arrive
       ↓
User reviews each image: thumbs up / thumbs down / notes
       ↓
Rejected images regenerated with edited prompts or swapped to reusable assets
       ↓
Composite images built: title text, overlay, position (left/center) — editable on canvas
       ↓
Feature, banners, mobile, GMB built — all editable: crop drag, title text, position
       ↓
Final confirmation → download ZIP (PNG + JPEG, correct folder structure + naming)
```

---

## Page Structure

### 1. Article Submission Panel
- Paste article text directly OR connect to the article library (already in app)
- Auto-extracts: title, H2 headings, theme label, selling flag, GMB cities
- User can override any extracted field before generation starts
- Shows manifest preview: numbered list of every image that will be created, with type tag (regular / bottom-line / faq / feature / banner / mobile / gmb)

---

### 2. Generation Panel — Backgrounds

**Real-time streaming:** Images appear on screen as each one finishes generating. You are not waiting for all 9 before seeing anything.

**Each section card shows:**
- Section number and H2 title
- Image type badge: REGULAR / BOTTOM-LINE / FAQ / FEATURE
- The prompt used (Gemini) or search term used (Pexels) — visible, readable, copy-able
- The generated/fetched background image
- Thumbs up / thumbs down buttons
- Notes field (optional — add context for why it's good or bad)
- Rerun button: regenerate with the same prompt
- Edit prompt button: opens prompt editor → rerun with your version
- Swap source button: toggle between Gemini AI / Pexels / Reusable Assets

**Prompt editor:**
- Full editable text field with the current prompt pre-populated
- One-click rerun after editing
- "Save as template" button — stores this prompt variant under the section type for future articles

**For FAQ and selling article sections:**
- Shows the reusable asset pool instead of a generated image
- Grid of all available pool images with click-to-select
- No generation, no prompt — just pick and confirm

---

### 3. Composite Editor Panel — Article Images

After backgrounds are approved, each article image is composited (1920×1080). Each card is fully editable.

**Per image card:**
- Final composited image (background + overlay + title text)
- Position toggle: LEFT / CENTER (one click — recomposes instantly)
- Title text editor: click the title in the preview to edit it inline
- Filename field: editable, shows exactly what the file will be named
- Crop adjustment: drag the background layer within the fixed frame to reposition
- Recompose button: applies all edits
- Approve / reject toggle

**Visual layout of each card:**
```
┌─────────────────────────────────────────┐
│  [Composited image — full preview]      │
│                                         │
│  Position:  [ LEFT ]  [ CENTER ]        │
│  Title:     [___editable text___]       │
│  Filename:  [___editable filename___]   │
│  [Crop]  [Recompose]  [✓ Approve]       │
└─────────────────────────────────────────┘
```

---

### 4. Composite Editor Panel — Feature, Banners, GMB

**Feature Image (700×450):**
- Drag-to-crop background layer on canvas
- Theme label: editable text field (defaults from manifest)
- Article title: editable text field (defaults from manifest)
- Overlay auto-selected (2-line vs 3-line) based on title wrap — shown as label
- Live preview updates as you type or crop

**Desktop Banner (1286×300) and Mobile Banner (400×600):**
- Drag-to-crop canvas — this is where the sign positioning happens visually instead of by pixel-guessing
- For sign-based images: "Find sign" button runs red pixel detection and auto-crops to it
- Manual fine-tune with arrow nudge buttons (±10px, ±50px) after auto-crop
- No text on banners — preview reflects final output exactly

**GMB Images (1200×900 × 4 cities):**
- Shared crop: adjust once, applies to all 4 cities simultaneously (or unlink to set individually)
- Title text: editable (shared across all cities)
- Preview shows all 4 city overlays in a 2×2 grid
- Filename for each city shown and editable

---

### 5. Reusable Assets Library

A dedicated bucket inside the app — always accessible from any step of the process.

**What it contains:**
- Home for sale pool (currently 8 images) — tagged: `[selling]`
- FAQ pool (currently 2 images) — tagged: `[faq]`
- Bottom-line pool — tagged: `[bottom-line]`
- Any image marked as "save to library" from a previous generation session

**Features:**
- Thumbnail grid with tags and labels
- Click any image to use it as the background for any section
- Upload new images to the bucket (adds to the pool permanently)
- Tag management: add/remove tags per image
- Each image shows usage history: "Used in 3 articles"
- Download individual assets from the library

**Pool rules enforced automatically:**
- FAQ sections only show the FAQ pool in the selector — no generated images offered
- Selling article feature/banner/GMB sections default to the selling pool and show it first
- Bottom-line sections for selling articles show the selling pool

**Why this matters:**
The reusable assets are the brand-safe, pre-approved foundation. They should be a first-class object in the app, not files buried in a references folder. Putting them in the app makes them instantly accessible, uploadable, and expandable without touching the file system.

---

### 6. Prompt Template Library

Built from your thumbs up/down history and explicit saves.

**Each template record contains:**
- Section type (equity / credit / renewal / warning / reset / etc.)
- Prompt text
- Source (Gemini / Pexels search term)
- Rating (average across uses)
- Times used
- Last used date
- Notes

**In the generation panel:**
- When a section type is recognized, the top-rated template for that type is pre-loaded
- You can browse other templates for the same type before generating
- After generation, your thumbs up/down updates the template's rating

**Why this matters:**
After 10–15 articles you will have a library of proven prompts for every section type that appear in Ross's content. New articles auto-populate with your best prompts instead of starting from scratch. The quality improves automatically over time without extra effort.

---

### 7. Session Management

Every article image job is a session.

**Session features:**
- Auto-saved — close browser, come back later, everything is where you left it
- Session list with status: In Progress / Awaiting Review / Complete
- Re-open any past session to regenerate, download again, or swap assets
- Article title, date, and thumbnail shown in the session list

**Session states:**
```
DRAFT → GENERATING → REVIEWING → EDITING → COMPLETE
```

---

### 8. Download

Once all images are approved:

- **Download ZIP** — contains both PNG and JPEG versions, correct folder structure:
  ```
  Images - {Article Title}/
  ├── final selection/
  │   ├── Feature Image - {title}.png/.jpg
  │   ├── Banner - {title}.png/.jpg
  │   ├── Mobile - {title}.png/.jpg
  │   ├── AskRoss.ca - 1 - {h2}.png/.jpg
  │   ├── AskRoss.ca - 2 - {h2}.png/.jpg
  │   ├── ...
  │   └── BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/
  │       ├── Toronto - {title}.png/.jpg
  │       ├── Ottawa - {title}.png/.jpg
  │       ├── Richmond Hill - {title}.png/.jpg
  │       └── Mississauga - {title}.png/.jpg
  ```
- **Download individual image** — from any card at any step
- **Export options:** PNG only / JPEG only / Both
- **Quality setting:** default 95 for JPEG

---

## Enhancement Features (Beyond the Core)

### Prompt Performance Dashboard
- Aggregate view of all thumbs up / thumbs down across all sessions
- Broken down by section type, by source (Gemini vs Pexels), by prompt pattern
- Shows which section types have the highest rejection rate — where to invest in better prompts
- Exportable as CSV for deeper analysis

### Side-by-Side Regeneration Compare
- When you regenerate a section, old and new appear side by side
- Confirm to replace, or dismiss to keep original
- Prevents the current problem of overwriting before deciding

### Batch Regenerate Bad
- One button: "Regenerate all rejected" — queues all thumbs-down sections for rerun
- Shows progress as each one comes back
- You review them as a group

### Article Library Integration
- Pull articles directly from the existing Ask Ross library instead of pasting
- One click from the article → starts the image creation session
- Completed sessions link back to the article record

### Image History Per Session
- Every generated version of every image is stored (not just the final one)
- You can roll back to a previous version at any time
- Shows a filmstrip of iterations per section

### Selling Article Auto-Detection
- Flags the article automatically if it detects selling keywords in the title
- Shows a banner: "This looks like a selling article — home for sale pool will be used for feature, banner, GMB, and bottom-line. Confirm?"
- You can override if detection is wrong

### Seasonal Prompt Guard
- System knows the current month
- Before generating, flags any section where the stored prompt template references the wrong season
- Prompts are auto-updated with the correct season before running

### Naming Convention Enforcer
- Before download, validates every filename against the naming rules
- Flags anything that doesn't match: `AskRoss.ca - {n} - {sanitized title}.{ext}`
- Auto-fix button corrects all names in one click

---

## Technical Architecture

### Backend: FastAPI (Python)
Wraps the existing Python pipeline. Runs on Railway or Fly.io (not Vercel — Python services need a persistent runtime).

**Key endpoints:**
```
POST /sessions                    — create new session from article text
GET  /sessions/{id}               — get session state
POST /sessions/{id}/generate      — start background generation
GET  /sessions/{id}/stream        — SSE stream of generation progress
POST /sessions/{id}/sections/{n}/recompose  — recompose one section
POST /sessions/{id}/sections/{n}/regenerate — regenerate one background
GET  /sessions/{id}/download      — return ZIP file
GET  /assets/library              — list reusable asset pool
POST /assets/library              — upload new pool image
GET  /prompts/templates           — list prompt templates by section type
POST /prompts/templates           — save prompt as template
POST /prompts/templates/{id}/rate — thumbs up/down
```

### Frontend: Next.js (existing app)
New page: `/image-studio` or `/content/images`

**Key libraries:**
- **Fabric.js or Konva.js** — canvas drag-to-crop editor
- **EventSource API** — consuming the SSE generation stream
- **JSZip** — client-side ZIP assembly or stream from backend

### Storage
- **Session data:** PostgreSQL or SQLite (session state, ratings, notes, prompt history)
- **Generated images:** S3-compatible bucket (Cloudflare R2 recommended — cheaper than AWS S3)
- **Reusable asset pool:** Same S3 bucket under `/assets/pool/`
- **Composed outputs:** Same bucket under `/sessions/{id}/output/`

### Asset Bucket Structure
```
r2://askross-images/
├── assets/
│   ├── pool/
│   │   ├── home-for-sale/
│   │   │   ├── home-for-sale-1.png
│   │   │   └── home-for-sale-7.png
│   │   ├── faq/
│   │   │   ├── faq-1.png
│   │   │   └── faq-2.png
│   │   └── bottom-line/
│   │       └── ...
│   └── overlays/
│       ├── article-overlay.png
│       ├── bottom-line-overlay.png
│       ├── feature-overlay-2line.png
│       └── ...
├── sessions/
│   └── {session-id}/
│       ├── manifest.json
│       ├── generated/
│       └── output/
└── templates/
    └── prompts.json
```

---

## Build Order

Build in this sequence — each phase is independently useful.

| Phase | What gets built | Value unlocked |
|---|---|---|
| 1 | FastAPI backend wrapping existing pipeline | Can generate images via API |
| 2 | Basic Next.js page: submit article → see generated images | Replaces CLI entirely |
| 3 | Review UI: thumbs up/down, notes, rerun | Structured feedback replaces manual folder sorting |
| 4 | Composite editor: position toggle, title edit | No more CLI recompositing |
| 5 | Canvas crop editor | Banner/mobile crop without pixel-guessing |
| 6 | Reusable assets library | Pool images accessible in app, uploadable |
| 7 | Download with correct folder structure | Full deliverable from browser |
| 8 | Prompt template library | Self-improving prompt quality over time |
| 9 | Session persistence + history | Never lose progress, revisit past jobs |
| 10 | Dashboard + analytics | Prompt performance visibility |

---

## One Note on "Jomai"

You mentioned AI generation via "Jomai" — want to confirm you mean **Gemini** (currently Google Gemini 2.5 Flash via OpenRouter). If there's a different service you want to plug in, let me know and I'll add it to the architecture. The backend is designed to swap generation sources without touching the frontend.

---

## What We Need to Start

1. **Access to the existing app codebase** (GitHub repo) — to understand the current page structure, auth, data layer, and component patterns before building the new page
2. **Confirm the hosting target for the backend** — Railway, Fly.io, or something else already in use
3. **Confirm the storage solution** — Cloudflare R2 is the recommendation but open to whatever is already set up
4. **Clarify "Jomai"** — confirm the generation source

Once those are answered, Phase 1 (FastAPI backend) can start immediately.
