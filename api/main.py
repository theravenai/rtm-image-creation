"""
main.py — FastAPI application entry point for the AskRoss Blog Image API.

Usage:
  cd api
  uvicorn main:app --reload --port 8000

Environment variables (same .env as parent directory):
  OPENROUTER_IMAGE_API_KEY   — Gemini image generation via OpenRouter
  PEXELS_API_KEY             — Pexels photo search

Static files:
  Served at /files/  from  ./storage/sessions/  (for session images)
  Also served from  ./storage/assets/           (for pool image uploads)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .pipeline import load_env
from .routers import assets, prompts, sessions
from .storage import ASSETS_DIR, SESSIONS_DIR, STORAGE_DIR, _ensure_dirs

# Ensure storage directories exist at import time so StaticFiles can mount them
_ensure_dirs()
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "pool_images").mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create storage directories and load environment variables."""
    _ensure_dirs()

    # Also ensure sessions and assets directories exist
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "pool_images").mkdir(parents=True, exist_ok=True)

    # Load .env from parent directory
    load_env()

    print("AskRoss Blog Image API started.")
    print(f"  Storage: {STORAGE_DIR}")
    print(f"  OPENROUTER_IMAGE_API_KEY: {'set' if os.environ.get('OPENROUTER_IMAGE_API_KEY') else 'NOT SET'}")
    print(f"  PEXELS_API_KEY:           {'set' if os.environ.get('PEXELS_API_KEY') else 'NOT SET'}")

    yield

    print("AskRoss Blog Image API shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AskRoss Blog Image API",
    description="REST API for the AskRoss.ca blog image compositing pipeline.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow all origins (Next.js dev + prod)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static file serving — session images and pool assets
# ---------------------------------------------------------------------------

# Mount the entire storage directory so both sessions/ and assets/ sub-paths work
app.mount(
    "/files",
    StaticFiles(directory=str(STORAGE_DIR)),
    name="files",
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(sessions.router)
app.include_router(assets.router)
app.include_router(prompts.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "openrouter_key": bool(os.environ.get("OPENROUTER_IMAGE_API_KEY")),
        "pexels_key":     bool(os.environ.get("PEXELS_API_KEY")),
    }
