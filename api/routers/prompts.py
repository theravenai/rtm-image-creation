"""
prompts.py — Prompt template management router for the AskRoss Blog Image API.

Endpoints:
  GET  /prompts/templates                      — list templates (optional ?section_type=)
  POST /prompts/templates                      — save a new template
  POST /prompts/templates/{id}/rate            — thumbs up/down {rating: 1|-1}
  GET  /prompts/templates/best/{section_type}  — top-rated template for a section type
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models import PromptTemplate, TemplateRating
from ..storage import (
    best_template,
    get_template,
    list_templates,
    rate_template,
    save_template,
)

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# GET /prompts/templates — list (optionally filtered)
# ---------------------------------------------------------------------------

@router.get("/templates")
async def list_prompt_templates(
    section_type: Optional[str] = Query(None, description="Filter by section type"),
):
    """Return all templates, optionally filtered by section_type.

    Valid section_type values: regular | bottom_line | faq | feature
    """
    return list_templates(section_type=section_type)


# ---------------------------------------------------------------------------
# GET /prompts/templates/best/{section_type} — top-rated
# NOTE: this route must be declared BEFORE /{template_id} to avoid shadowing
# ---------------------------------------------------------------------------

@router.get("/templates/best/{section_type}")
async def get_best_template(section_type: str):
    """Return the highest-rated template for a section type.

    Returns 404 if no rated templates exist for this section type.
    """
    tmpl = best_template(section_type)
    if tmpl is None:
        raise HTTPException(
            status_code=404,
            detail=f"No rated templates found for section_type='{section_type}'",
        )
    return tmpl


# ---------------------------------------------------------------------------
# POST /prompts/templates — save new template
# ---------------------------------------------------------------------------

@router.post("/templates")
async def create_prompt_template(body: PromptTemplate):
    """Save a new prompt template. Generates a UUID if no id is provided."""
    tmpl = body.model_dump()
    if not tmpl.get("id"):
        tmpl["id"] = str(uuid.uuid4())
    if not tmpl.get("created_at"):
        tmpl["created_at"] = _now_iso()

    saved = save_template(tmpl)
    return saved


# ---------------------------------------------------------------------------
# POST /prompts/templates/{id}/rate — thumbs up/down
# ---------------------------------------------------------------------------

@router.post("/templates/{template_id}/rate")
async def rate_prompt_template(template_id: str, body: TemplateRating):
    """Apply a rating (+1 thumbs up, -1 thumbs down) to a template."""
    if body.rating not in (-1, 1):
        raise HTTPException(status_code=422, detail="Rating must be 1 or -1")

    updated = rate_template(template_id, body.rating)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    return updated
