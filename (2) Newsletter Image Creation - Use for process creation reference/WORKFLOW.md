# Newsletter Image Creation — Workflow

> This diagram covers the complete image creation process for every newsletter issue.
> Render with any Markdown viewer that supports Mermaid (VS Code, GitHub, Obsidian, etc.)

---

```mermaid
flowchart TD
    START([📩 Receive complete newsletter]) --> FOLDER[📁 Create issue folder\nmkdir out/{issue-folder}\nAll scripts use --output-dir]
    FOLDER --> B1

    %% ─────────────────────────────────────────
    %% STAGE 1 — BANNER
    %% ─────────────────────────────────────────
    B1{Is the newsletter about a\nnamed politician or\nmajor world event?}

    B1 -- YES --> SONAR[🔎 Sonar Banner\nbuild_newsletter_banner.py\n--source sonar\nBrowse candidates, pick best,\nno-text rule applies]
    B1 -- NO  --> DUAL[Build TWO banner options]

    DUAL --> PEXELS_B[📷 Pexels Banner\n--source pexels\nStock photo matching topic]
    DUAL --> AI_B[🤖 AI Banner\n--source ai\nArt Director prompt\nGemini 2.5 Flash Image]

    SONAR      --> TEXT_B{Add text\nto banner?}
    PEXELS_B   --> TEXT_B
    AI_B       --> TEXT_B

    TEXT_B -- Ross Taylor\nPolitician\nPowerful editorial --> NOTEXT[--no-text]
    TEXT_B -- Abstract / scene\nno prominent person --> CENTER[--text-position center]
    TEXT_B -- People in\nlower half --> UPPERLEFT[--text-position upper-left\ny=213]
    TEXT_B -- People in\nupper half --> LOWERLEFT[--text-position lower-left\ny≈550]

    NOTEXT    --> BANNER_SEND
    CENTER    --> BANNER_SEND
    UPPERLEFT --> BANNER_SEND
    LOWERLEFT --> BANNER_SEND

    BANNER_SEND([📤 Send banner options for approval])
    BANNER_SEND --> BANNER_OK{Approved?}

    BANNER_OK -- Revise title --> TEXT_B
    BANNER_OK -- Regenerate image\nor pick different\nSonar candidate --> DUAL
    BANNER_OK -- ✅ Approved --> BANNER_LOCKED([🔒 Banner Raw locked\nout/{name} Banner Raw.png])

    %% ─────────────────────────────────────────
    %% STAGE 2 — GMB SHARE
    %% ─────────────────────────────────────────
    BANNER_LOCKED --> GMB[Build GMB Share\nbuild_newsletter_custom.py\n--banner-image out/{name} Banner Raw.png\nWrite title1 + intro]

    GMB --> GMB_SEND([📤 Send GMB Share for approval\nReview: title1 + intro text])
    GMB_SEND --> GMB_OK{Approved?}

    GMB_OK -- Revise title or intro --> GMB
    GMB_OK -- ✅ Approved --> GMB_LOCKED([🔒 GMB Share locked\nout/{title1} GMB Share.png])

    %% ─────────────────────────────────────────
    %% STAGE 3 — SECTION IMAGES
    %% ─────────────────────────────────────────
    GMB_LOCKED --> SECTIONS[Build section images\none per newsletter section]

    SECTIONS --> SEC_TYPE{Section type?}

    SEC_TYPE -- Article on\ncanadianmortgagetrends.com --> CMT_SEC[CMT Section\nCMT logo overlay]
    SEC_TYPE -- Ask Ross article\nclient story\nnewsletter insert --> AR_SEC[Ask Ross Section\nAskRoss grey scrim overlay]

    CMT_SEC --> CMT_A[Option A: Fetch OG image\n--source cmt --cmt-url]
    CMT_SEC --> CMT_B[Option B: Pexels\n--source pexels --section-type cmt]

    AR_SEC --> AR_AI[AI generated only\n--source ai --section-type askross\nWide 16:4 panoramic prompt]

    CMT_A  --> FACE_CHECK{Faces cut off?}
    CMT_B  --> FACE_CHECK
    AR_AI  --> FACE_CHECK

    FACE_CHECK -- YES → pick different\nimage or regenerate --> SEC_TYPE
    FACE_CHECK -- NO ✅ --> SEC_SEND

    SEC_SEND([📤 Send all section images for approval\nCMT: 2 options — Ask Ross: 1 option])
    SEC_SEND --> SEC_OK{Approved?}

    SEC_OK -- Revise → regenerate\nor different query --> SEC_TYPE
    SEC_OK -- ✅ Approved → keep file --> CLEANUP[🗑️ Delete any rejected assets]
    CLEANUP --> DONE([✅ All images complete and approved])
```

---

## Quick command reference

### Before anything — create issue folder

```bash
mkdir "out/Issue Folder Name"
# All commands below append: --output-dir "out/Issue Folder Name"
```

### Stage 1 — Banner

```bash
# Sonar (politician / world event) — browse first, then build
python "(1) Banner Images/build_newsletter_banner.py" --source sonar \
  --sonar-query "Mark Carney 2025" --list-images --recency week
python "(1) Banner Images/build_newsletter_banner.py" --source sonar \
  --sonar-query "Mark Carney 2025" --use-cache --image-index 1 \
  --name "Carney Housing Win" --no-text \
  --output-dir "out/Carney Housing Win"

# AI banner (lifestyle / housing / abstract)
python "(1) Banner Images/build_newsletter_banner.py" --source ai \
  --banner-prompt "Wide 16:8 panoramic, spring Canadian neighbourhood..." \
  --name "Spring 2025 Market" \
  --title "Is now the right time to buy a home in Canada?" \
  --text-position upper-left \
  --output-dir "out/Spring 2025 Market"

# Pexels banner (always build alongside AI for non-Sonar)
python "(1) Banner Images/build_newsletter_banner.py" --source pexels \
  --pexels-query "spring Canada neighbourhood real estate" \
  --name "Spring 2025 Market Pexels" \
  --title "Is now the right time to buy a home in Canada?" \
  --text-position center \
  --output-dir "out/Spring 2025 Market"

# Text/title tweak only (reuse existing raw)
python "(1) Banner Images/build_newsletter_banner.py" --source custom \
  --banner-image "out/Spring 2025 Market/Spring 2025 Market Banner Raw.png" \
  --name "Spring 2025 Market" \
  --title "New title here" --text-position upper-left \
  --output-dir "out/Spring 2025 Market"
```

### Stage 2 — GMB Share

```bash
# Standard: use approved Banner Raw as input
python "(2) GMB Share Images/build_newsletter_custom.py" \
  --banner-image "out/Spring 2025 Market/{name} Banner Raw.png" \
  --title1 "Your Spring Advantage: Play the Market Before It Plays You" \
  --intro "Spring is here and the Canadian housing market is moving..." \
  --output-dir "out/Spring 2025 Market"
```

### Stage 3 — Section Images

```bash
# CMT section — Option A (article OG image)
python "(3) Section Images/build_newsletter_section.py" --source cmt \
  --cmt-url "https://www.canadianmortgagetrends.com/article-slug/" \
  --name "Retirement Mortgage CMT" \
  --output-dir "out/Spring 2025 Market"

# CMT section — Option B (Pexels — always build this for CMT)
python "(3) Section Images/build_newsletter_section.py" --source pexels \
  --pexels-query "retirement couple Canadian home" \
  --section-type cmt --name "Retirement Mortgage Pexels" \
  --output-dir "out/Spring 2025 Market"

# Ask Ross section — AI only (default)
python "(3) Section Images/build_newsletter_section.py" --source ai \
  --banner-prompt "Wide 16:4 panoramic, Bank of Canada Ottawa, dramatic sky, no text" \
  --section-type askross --name "BoC Rate AI" \
  --output-dir "out/Spring 2025 Market"
```

---

## Approval gates summary

| Stage | What gets reviewed | Actions on rejection |
|---|---|---|
| Banner | Image composition + title text | Regenerate image, adjust title, pick different Sonar candidate, change text position |
| GMB Share | Title1 text + intro copy | Rewrite title/intro, rerun script |
| Section Images | Image content + face crops | Regenerate, change Pexels query, use different photo index |

**After final approval:**
- Keep all approved files in `out/`
- Delete rejected asset files from `out/`

---

## Decision tables

### Banner source

| Newsletter topic | Source |
|---|---|
| Named politician, major world event, war, election | Sonar |
| Everything else | AI (Gemini) + Pexels — build both |

### Banner text position

| What's in the image | Position |
|---|---|
| Ross Taylor | No text |
| Named politician / powerful editorial | No text |
| No prominent people — abstract, landscape, scene | Center |
| People in lower half, space above | Upper-left (y=213) |
| People in upper half, space below | Lower-left (y≈550) |

### Section type

| Section covers | Type | Overlay | Options |
|---|---|---|---|
| canadianmortgagetrends.com article | CMT | CMT logo | Article OG + Pexels |
| Ask Ross article, client story, insert | Ask Ross | Grey scrim | AI only |
