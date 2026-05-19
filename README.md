# RTM Blog Image Creation

Image assets, templates, and generation scripts for AskRoss.ca blog posts and newsletter issues.

---

## Repo structure

```
BLOG IMAGE CREATION/
├── (1) Complete Blog Article Images Sample/   ← reference examples of finished blog images
├── BLOG POST - Banner Images/                 ← banner image templates and samples
├── BLOG POST - Feature Image/                 ← feature image templates and samples
├── BLOG POST - Large Article Images for Askross.ca/  ← reusable in-article image assets
├── BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/ ← GMB reshare templates
│
├── (2) Newsletter Image Creation/             ← scripts + specs for generating newsletter images
│   ├── (1) Banner Images/                     ← banner script + spec + samples
│   ├── (2) GMB Share Images/                  ← GMB share scripts + specs (4 sources)
│   ├── (3) Section Images/                    ← section image script + spec
│   ├── in/                                    ← custom input images
│   ├── out/                                   ← all generated output images
│   ├── .env                                   ← API keys
│   ├── requirements.txt
│   ├── MASTER ARCHITECTURE.md                 ← full technical reference
│   └── WORKFLOW.md                            ← step-by-step workflow + Mermaid diagram
│
└── SOP_ Create Blog Article Images and Social Share Assets.pdf
```

---

## Newsletter image creation

The `(2) Newsletter Image Creation/` folder contains Python scripts that generate three types of images per newsletter issue.

### Prerequisites

```bash
pip install -r "(2) Newsletter Image Creation/requirements.txt"
```

Add your API keys to `(2) Newsletter Image Creation/.env`:

```
OPENROUTER_IMAGE_API_KEY=...   # Gemini 2.5 Flash Image via OpenRouter
PERPLEXITY_API_KEY=...         # Sonar image search
PEXELS_API_KEY=...             # Pexels stock photos
```

### The three image types

| Type | Canvas | Script | When |
|---|---|---|---|
| Banner | 1200 × 800 px | `(1) Banner Images/build_newsletter_banner.py` | One per issue — built first |
| GMB Share | 1200 × 900 px | `(2) GMB Share Images/build_newsletter_custom.py` | One per issue — built after banner approval |
| Section | 1200 × 400 px | `(3) Section Images/build_newsletter_section.py` | One per newsletter section |

### Workflow overview

**1. Create an issue folder**
```bash
mkdir "(2) Newsletter Image Creation/out/Issue Name"
# Use --output-dir "out/Issue Name" on every script call
```

**2. Build the banner**
```bash
# For politician / world event topics — use Sonar
python "(2) Newsletter Image Creation/(1) Banner Images/build_newsletter_banner.py" \
  --source sonar --sonar-query "Mark Carney 2025" --list-images

# For everything else — build AI and Pexels options, present both for approval
python "(2) Newsletter Image Creation/(1) Banner Images/build_newsletter_banner.py" \
  --source ai --banner-prompt "..." --name "Spring 2025 Market" \
  --title "Is now the right time to buy?" --text-position upper-left \
  --output-dir "out/Spring 2025 Market"
```

**3. Build the GMB Share (using approved banner raw)**
```bash
python "(2) Newsletter Image Creation/(2) GMB Share Images/build_newsletter_custom.py" \
  --banner-image "out/Spring 2025 Market/Spring 2025 Market Banner Raw.png" \
  --title1 "Your Spring Advantage" --intro "Spring is here and the market is moving..." \
  --output-dir "out/Spring 2025 Market"
```

**4. Build section images**
```bash
# CMT article section (build OG image + Pexels, present both)
python "(2) Newsletter Image Creation/(3) Section Images/build_newsletter_section.py" \
  --source cmt --cmt-url "https://canadianmortgagetrends.com/article/" \
  --name "Section Name" --output-dir "out/Spring 2025 Market"

# Ask Ross section (AI only)
python "(2) Newsletter Image Creation/(3) Section Images/build_newsletter_section.py" \
  --source ai --section-type askross --name "Section Name" \
  --output-dir "out/Spring 2025 Market"
```

For full command reference and decision tables, see [`MASTER ARCHITECTURE.md`](<(2) Newsletter Image Creation - Use for process creation reference/MASTER ARCHITECTURE.md>) and [`WORKFLOW.md`](<(2) Newsletter Image Creation - Use for process creation reference/WORKFLOW.md>).
