"""
create_folder_structure.py — Create the output folder hierarchy for a blog article.

Output structure:
  {base_output_dir}/Blog Images - {article_title}/
  ├── Feature Image - {article_title}.png              (created by compose_feature)
  ├── {article_title} - Feature Background RAW.png     (created by compose_feature)
  ├── Banner - {article_title}.png                     (created by compose_banners)
  ├── Mobile - {article_title}.png                     (created by compose_banners)
  ├── BLOG POST - Large Article Images for Askross.ca/ (created here)
  │   └── AskRoss.ca - {H2 title}.png
  └── BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE/(created here)
      ├── Toronto - {article_title}.png
      ├── Ottawa - {article_title}.png
      ├── Richmond Hill - {article_title}.png
      └── Mississauga - {article_title}.png
"""

import os
from pathlib import Path

from .shared import sanitize_filename


ARTICLE_IMAGES_SUBDIR = "BLOG POST - Large Article Images for Askross.ca"
GMB_SUBDIR = "BLOG RESHARE - GMB - POST ONLY- IMAGES TEMPLATE"


def create_output_folder_structure(
    base_output_dir: str,
    article_title: str,
) -> dict:
    """Create all required output subdirectories and return their paths.

    Args:
        base_output_dir:  Parent directory (e.g. 'out/test-output' or 'out').
        article_title:    Full H1 article title (not sanitized).

    Returns:
        Dict with keys:
          - root:          Blog Images - {title}/ directory
          - article_images: Subdirectory for article H2 images
          - gmb:           Subdirectory for GMB images
    """
    safe_title = sanitize_filename(article_title)
    root_dir = os.path.join(base_output_dir, f"Blog Images - {safe_title}")
    article_images_dir = os.path.join(root_dir, ARTICLE_IMAGES_SUBDIR)
    gmb_dir = os.path.join(root_dir, GMB_SUBDIR)

    for d in [root_dir, article_images_dir, gmb_dir]:
        os.makedirs(d, exist_ok=True)
        print(f"  Created dir: {d}")

    return {
        "root": root_dir,
        "article_images": article_images_dir,
        "gmb": gmb_dir,
    }
