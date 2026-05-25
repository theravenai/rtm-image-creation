# AskRoss Blog Image API

FastAPI backend that wraps the existing Python image compositing pipeline and exposes it as a REST API for the Next.js frontend.

## Quick Start

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

## Environment Variables

The API reads the same `.env` file as the parent pipeline scripts. Place a `.env` in the parent directory (`BLOG IMAGE CREATION/`) or the fallback newsletter reference directory.

Required variables:

| Variable | Purpose |
|---|---|
| `OPENROUTER_IMAGE_API_KEY` | Gemini image generation via OpenRouter |
| `PEXELS_API_KEY` | Pexels photo search for Pexels source mode |

## Running as a package

Because `main.py` uses relative imports (`from .routers import ...`), you must run it as a module from the **parent** directory:

```bash
# From BLOG IMAGE CREATION/ (parent of api/)
uvicorn api.main:app --reload --port 8000
```

Or from inside the `api/` directory using the package form:

```bash
cd ..   # go to BLOG IMAGE CREATION/
python -m uvicorn api.main:app --reload --port 8000
```

## API Endpoints

### Health
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Check API status and env vars |

### Sessions
| Method | Path | Description |
|---|---|---|
| GET | `/sessions/` | List all sessions |
| POST | `/sessions/` | Create session from article text |
| GET | `/sessions/{id}` | Get full session detail |
| DELETE | `/sessions/{id}` | Delete session |
| GET | `/sessions/{id}/stream` | SSE: run full generation pipeline |
| POST | `/sessions/{id}/sections/{n}` | Update section metadata |
| POST | `/sessions/{id}/sections/{n}/regen` | Regenerate background |
| POST | `/sessions/{id}/sections/{n}/composite` | Recomposite with current settings |
| GET | `/sessions/{id}/download` | Download ZIP of all (or approved) images |

### Assets
| Method | Path | Description |
|---|---|---|
| GET | `/assets/pool` | List pool images |
| POST | `/assets/pool/upload` | Upload new pool image |
| PUT | `/assets/pool/{id}` | Update tags/name |
| DELETE | `/assets/pool/{id}` | Remove from pool |

### Prompts
| Method | Path | Description |
|---|---|---|
| GET | `/prompts/templates` | List templates (optional `?section_type=`) |
| POST | `/prompts/templates` | Save new template |
| POST | `/prompts/templates/{id}/rate` | Rate template (+1/-1) |
| GET | `/prompts/templates/best/{section_type}` | Best template for type |

## SSE Stream Format

Connect to `GET /sessions/{id}/stream` with `Accept: text/event-stream`.

Each event has `data:` as a JSON object with a `type` field:

```json
{"type": "section_start", "section_number": 2, "h2_text": "...", "index": 0, "total": 7}
{"type": "section_done",  "section_number": 2, "url": "/files/...", "prompt": "...", "source": "gemini"}
{"type": "section_error", "section_number": 3, "error": "..."}
{"type": "all_done",      "status": "done", "errors": [], "total": 7}
```

Query param `?source=pexels` uses Pexels photos instead of Gemini generation.

## Storage Layout

```
api/storage/
  sessions/
    {uuid}/
      session.json            — full session + manifest + section metadata
      sections/
        {section_number}/
          background.png      — raw generated/fetched background
          composited.png      — final composited image with text/overlay
  assets/
    pool.json                 — metadata for uploaded pool images
    pool_images/              — uploaded image files
  prompts/
    templates.json            — saved/rated prompt templates
```

Static files are served at `/files/` — so `/files/sessions/{id}/sections/{n}/composited.png` maps directly to the composited image URL.
