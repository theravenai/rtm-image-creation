# Ask Ross Newsletter — Section Image Spec

**For:** Raven AI agent (Claude Code) — newsletter section image workflow
**Output:** 1200 × 400 PNG per section, saved in `out/`
**Script:** `build_newsletter_section.py`
**When to use:** After the banner is approved. Build one section image per newsletter section.

---

## What is a section image?

Each newsletter section covers either one or two articles. The section image is a wide 1200×400 panoramic that sits above that section in the newsletter. It is purely visual — **no title text is rendered on the image**. The logo overlay identifies the content source.

---

## Faces rule (absolute — never break)

**If people appear in the image, their faces must never be cut off.**

- Portrait-oriented source images use top-anchored cropping (faces near the top are preserved).
- Landscape-oriented source images use center cropping.
- If a selected image still cuts off faces after cropping, pick a different photo or query.

---

## Two section types

### Type 1 — CMT (Canadian Mortgage Trends) article
Used when the section covers an article Ross wrote for canadianmortgagetrends.com.

- **Option A:** Fetch the feature/OG image directly from the CMT article URL
- **Option B:** Pexels stock photo that reflects the article topic
- **Overlay:** `(3) Section Images/overlays/CMT logo.png` — CMT logo box in bottom-left corner
- **Always provide both options** — CMT article image + Pexels

### Type 2 — Ask Ross article / section insert
Used when the section covers an Ask Ross article, a client story, or a newsletter-only insert.

- **Option A (default):** AI-generated image matching the article topic
- **Option B (only if requested):** Pexels stock photo
- **Overlay:** `(3) Section Images/overlays/AskRoss Logo + Grey Transparent Layer.png` — grey scrim + ASKROSS.CA logo top-left
- **Default: build AI option only.** Build Pexels only if the operator asks.

---

## Decision: which type?

| Section content | Type | Overlay | Options to build |
|---|---|---|---|
| Article published on canadianmortgagetrends.com | CMT | CMT logo | Article OG image + Pexels |
| Ask Ross article, client story, newsletter insert | Ask Ross | AskRoss grey scrim | AI only (Pexels on request) |

---

## Workflow (every section)

```
Step 0 — Issue folder must already exist: out/{issue-folder}/
    All commands below append: --output-dir "out/{issue-folder}"

Step 1 — Identify section type (CMT or Ask Ross)

Step 2 — CMT sections: build both options
    Option A (article image):
        python build_newsletter_section.py --source cmt --cmt-url "..." \
            --name "Section Name CMT" --output-dir "out/{issue-folder}"
    Option B (Pexels):
        python build_newsletter_section.py --source pexels --pexels-query "..." \
            --section-type cmt --name "Section Name Pexels" --output-dir "out/{issue-folder}"

Step 3 — Ask Ross sections: build AI only
    python build_newsletter_section.py --source ai --banner-prompt "..." \
        --section-type askross --name "Section Name AI" --output-dir "out/{issue-folder}"

Step 4 — Present options for operator approval
    CMT: present both (article + Pexels)
    Ask Ross: present AI image; build Pexels only if requested

Step 5 — Approved image goes into the newsletter
```

**If the fetched CMT image cuts off faces or looks bad at 1200×400, use the Pexels option instead.**

---

## AI prompt guidance

Use `prompt-builder.md` (in this folder) to craft the `--banner-prompt` argument for AI-generated section images. It contains the Art Director system prompt — scene modes, positive/negative attributes, Canadian setting markers, and framing rules. Follow it the same way you would for banner AI prompts; the only difference is the target aspect ratio is **16:4 panoramic** instead of 16:8.

---

## Image content guidelines

**CMT Option A (fetched):** Use the CMT article's OG/feature image as-is. If the image cuts off faces, is too small, or looks bad at 1200×400, fall back to the Pexels option.

**AI prompts:** Write a wide panoramic scene relevant to the article. No text in the image. No close-up faces. Think editorial stock photo style. Aspect ratio hint in the prompt: `wide 16:4 panoramic, no text`.

**Pexels queries:** Match the article topic closely. Prefer wide landscape-oriented photos. For finance/mortgage topics: Canadian home exteriors, families, signing documents, Canadian cityscapes.

---

## Canvas spec (locked)

- Canvas: **1200 × 400 px**, RGB output
- No text rendered on section images — image + overlay only
- Overlays:
  - CMT: `(3) Section Images/overlays/CMT logo.png` — logo in bottom-left, rest transparent
  - Ask Ross: `(3) Section Images/overlays/AskRoss Logo + Grey Transparent Layer.png` — grey scrim + top-left logo

---

## Step-by-step commands

### CMT article section

```bash
# Option A — fetch CMT feature image
python build_newsletter_section.py \
  --source cmt \
  --cmt-url "https://www.canadianmortgagetrends.com/article-slug/" \
  --name "Retirement Mortgage CMT"

# Option B — Pexels
python build_newsletter_section.py \
  --source pexels \
  --pexels-query "retirement couple Canadian home" \
  --section-type cmt \
  --name "Retirement Mortgage Pexels"
```

### Ask Ross article / insert section

```bash
# AI generated (default — build this only unless Pexels is requested)
python build_newsletter_section.py \
  --source ai \
  --banner-prompt "Wide 16:4 panoramic, Bank of Canada building Ottawa, dramatic sky, photorealistic, no text" \
  --section-type askross \
  --name "BoC Rate Decision AI"
```

### Reuse image, reapply overlay only

```bash
python build_newsletter_section.py \
  --source custom \
  --banner-image "out/BoC Rate Decision AI Section Raw.png" \
  --section-type askross \
  --name "BoC Rate Decision AI v2"
```

---

## All flags

| Flag | Purpose |
|---|---|
| `--source` | `cmt` / `ai` / `pexels` / `custom` — required |
| `--name` | Output filename stem — required |
| `--section-type` | `askross` or `cmt` — sets overlay. Auto-set for `--source cmt`. Required for pexels/ai/custom. |
| `--cmt-url` | `[cmt]` Full URL of the CMT article |
| `--banner-prompt` | `[ai]` Image generation prompt |
| `--pexels-query` | `[pexels]` Pexels search query |
| `--photo-index N` | `[pexels]` Which photo to use (default 0) |
| `--photo-count N` | `[pexels]` How many to fetch (default 15) |
| `--list-photos` | `[pexels]` Print results and exit |
| `--banner-image PATH` | `[custom]` Path to existing image |
| `--output-dir PATH` | Override output directory (default: `out/`) |

---

## Output files

All files land in the issue folder set by `--output-dir "out/{issue-folder}"`.

| File | Purpose |
|---|---|
| `out/{issue-folder}/{name} Section Raw.png` | 1200×400, no overlay — stored for potential reuse |
| `out/{issue-folder}/{name} Section.png` | 1200×400, overlay applied — the final section image |

---

## QC (automatic)

1. Output dimensions exactly `(1200, 400)`
2. Center pixel `(600, 200)` is not pure black (not blank)
3. Review: if people appear in image, confirm no faces are cut off — regenerate if so
