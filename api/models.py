"""
models.py — Pydantic request/response models for the AskRoss Blog Image API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Session models
# ---------------------------------------------------------------------------

class ArticleSubmission(BaseModel):
    article_text: str
    article_title: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    article_title: str
    status: str  # pending | generating | done | error
    manifest: Optional[dict] = None
    is_selling_article: bool = False
    created_at: str


class SectionUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=-1, le=1)   # -1 / 0 / 1
    notes: Optional[str] = None
    force_position: Optional[str] = None               # upper-left | lower-left | center
    filename: Optional[str] = None


class RegenRequest(BaseModel):
    prompt: Optional[str] = None
    source: str = "gemini"                             # gemini | pexels | pool
    pool_image_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Asset models
# ---------------------------------------------------------------------------

class AssetResponse(BaseModel):
    id: str
    name: str
    url: str
    tags: list[str] = []
    usage_count: int = 0


# ---------------------------------------------------------------------------
# Prompt template models
# ---------------------------------------------------------------------------

class PromptTemplate(BaseModel):
    id: Optional[str] = None
    section_type: str                    # regular | bottom_line | faq | feature
    source: str                          # gemini | pexels
    prompt: str
    rating_sum: int = 0
    rating_count: int = 0
    times_used: int = 0
    created_at: Optional[str] = None


class TemplateRating(BaseModel):
    rating: int = Field(..., ge=-1, le=1)  # 1 or -1
