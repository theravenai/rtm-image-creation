"""
seed_pool.py — Copy reusable pool images into api/storage and register them in pool.json.

Run once from the BLOG IMAGE CREATION directory:
  python -m api.seed_pool
"""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .storage import ASSETS_DIR, save_asset, list_assets

POOL_IMAGES_DIR = ASSETS_DIR / "pool_images"
POOL_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

PARENT = Path(__file__).parent.parent.resolve()
REF = PARENT / "references" / "BLOG POST - Large Article Images for Askross.ca" / "Reusable Image Large Article Image Assets"

POOL_SOURCES = [
    # (source_glob_or_path, tag)
    (REF / "home for sale options" / "*.png",           "selling"),
    (REF / "AskRoss.ca - All of the FAQs*.png",         "faq"),
    (REF / "AskRoss.ca - Bottom line*.png",              "bottom-line"),
    (REF / "AskRoss.ca - Resuable Bottom Line*.png",     "bottom-line"),
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def seed():
    # Collect existing filenames so we don't double-seed
    existing = {a.get("source_name") for a in list_assets()}
    seeded = 0

    for pattern, tag in POOL_SOURCES:
        import glob as gl
        files = sorted(gl.glob(str(pattern)))
        for src in files:
            src_path = Path(src)
            if src_path.name in existing:
                print(f"  skip (already seeded): {src_path.name}")
                continue

            asset_id = str(uuid.uuid4())
            dest = POOL_IMAGES_DIR / f"{asset_id}.png"
            shutil.copy2(src, dest)

            asset = {
                "id":          asset_id,
                "name":        src_path.stem,
                "source_name": src_path.name,
                "filename":    dest.name,
                "url":         f"/files/assets/pool_images/{dest.name}",
                "tags":        [tag],
                "usage_count": 0,
                "created_at":  now_iso(),
            }
            save_asset(asset)
            existing.add(src_path.name)
            seeded += 1
            print(f"  seeded [{tag}]: {src_path.name}")

    print(f"\nDone — {seeded} images seeded to {POOL_IMAGES_DIR}")


if __name__ == "__main__":
    seed()
