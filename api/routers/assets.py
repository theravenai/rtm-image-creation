"""
assets.py — Pool image asset management router for the AskRoss Blog Image API.

Endpoints:
  GET  /assets/pool              — list all pool images
  POST /assets/pool/upload       — upload a new pool image (multipart form)
  PUT  /assets/pool/{id}         — update tags / name
  DELETE /assets/pool/{id}       — remove from pool
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from ..models import AssetResponse
from ..storage import (
    ASSETS_DIR,
    delete_asset,
    get_asset,
    list_assets,
    save_asset,
)

router = APIRouter(prefix="/assets", tags=["assets"])

POOL_IMAGES_DIR = ASSETS_DIR / "pool_images"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _asset_to_response(asset: dict) -> dict:
    return {
        "id":          asset.get("id"),
        "name":        asset.get("name", ""),
        "url":         asset.get("url", ""),
        "tags":        asset.get("tags", []),
        "category":    asset.get("category", ""),
        "usage_count": asset.get("usage_count", 0),
        "created_at":  asset.get("created_at", ""),
    }


# ---------------------------------------------------------------------------
# GET /assets/pool
# ---------------------------------------------------------------------------

@router.get("/pool")
async def list_pool_assets():
    """Return all pool image asset metadata."""
    assets = list_assets()
    return [_asset_to_response(a) for a in assets]


# GET /assets/categories
@router.get("/categories")
async def list_categories():
    """Return sorted list of unique non-empty category names."""
    assets = list_assets()
    cats = sorted({a.get("category", "") for a in assets if a.get("category")})
    return cats


# ---------------------------------------------------------------------------
# POST /assets/pool/upload
# ---------------------------------------------------------------------------

@router.post("/pool/upload")
async def upload_pool_asset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # comma-separated
):
    """Upload a new image to the pool. Accepts PNG or JPEG."""
    if file.content_type not in ("image/png", "image/jpeg", "image/jpg"):
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: {file.content_type}. Must be PNG or JPEG.",
        )

    POOL_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    asset_id   = str(uuid.uuid4())
    ext        = ".png" if file.content_type == "image/png" else ".jpg"
    safe_name  = name or file.filename or f"asset_{asset_id}"
    filename   = f"{asset_id}{ext}"
    dest_path  = POOL_IMAGES_DIR / filename

    # Read, validate, and save
    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Cannot open image: {e}")

    img.save(str(dest_path), "PNG")

    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    asset = {
        "id":          asset_id,
        "name":        safe_name,
        "filename":    filename,
        "url":         f"/files/assets/pool_images/{filename}",
        "tags":        tag_list,
        "usage_count": 0,
        "width":       img.width,
        "height":      img.height,
        "created_at":  _now_iso(),
    }

    save_asset(asset)
    return _asset_to_response(asset)


# ---------------------------------------------------------------------------
# PUT /assets/pool/{id} — update tags / name
# ---------------------------------------------------------------------------

@router.put("/pool/{asset_id}")
async def update_pool_asset(
    asset_id: str,
    name: Optional[str] = None,
    tags: Optional[str] = None,   # comma-separated
    category: Optional[str] = None,
):
    asset = get_asset(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

    if name is not None:
        asset["name"] = name
    if tags is not None:
        asset["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    if category is not None:
        asset["category"] = category

    save_asset(asset)
    return _asset_to_response(asset)


# ---------------------------------------------------------------------------
# DELETE /assets/pool/{id}
# ---------------------------------------------------------------------------

@router.delete("/pool/{asset_id}")
async def delete_pool_asset(asset_id: str):
    asset = get_asset(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

    # Delete the file if it's stored in our managed pool directory
    filename = asset.get("filename", "")
    if filename:
        file_path = POOL_IMAGES_DIR / filename
        if file_path.exists():
            file_path.unlink()

    deleted = delete_asset(asset_id)
    return {"deleted": asset_id, "success": deleted}
