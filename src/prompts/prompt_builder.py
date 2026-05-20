"""
prompt_builder.py — Builds Gemini 2.5 Flash Image prompts for 1920x1080 article images.

Each H2 section uses its manifest `prompt_hint` as the scene description,
wrapped with Art Director composition constraints and negatives.

Returns None for bottom-line and FAQ sections (those use reusable images).
"""

import re

NEGATIVES = (
    "cropped heads, chins at bottom edge, excessive sky, distorted hands, "
    "plastic skin, fake smiles, business handshakes, American flags, palm trees, "
    "watermarks, busy upper-left, no logos, no signs, no readable text, "
    "illustration look, 3D render, AI artifacts"
)

_COMP_SUFFIX = (
    "upper-left kept visually quiet for logo overlay, "
    "lower-center clear for title text, "
    "16:9 wide aspect 1920x1080, photorealistic editorial photography"
)


def _wrap(prompt_hint: str) -> str:
    """Wrap a scene description with Art Director composition rules and negatives."""
    raw = f"{prompt_hint}, {_COMP_SUFFIX}, avoiding {NEGATIVES}."
    raw = re.sub(r" {2,}", " ", raw)
    raw = re.sub(r",{2,}", ",", raw)
    return raw.strip()


def build_article_prompt(section: dict):
    """Build a 1920x1080 prompt for a single H2 section.

    Returns None for bottom_line and faq sections (reusable images, no generation needed).
    Returns a prompt string for regular sections, using the manifest `prompt_hint`.
    """
    if section.get("is_bottom_line") or section.get("is_faq"):
        return None

    hint = section.get("prompt_hint", "")
    if hint:
        return _wrap(hint)

    # Fallback if no prompt_hint: generic Canadian mortgage professional scene
    return _wrap(
        "Medium shot of a Canadian homeowner couple in their 40s at a kitchen table "
        "reviewing mortgage documents, concerned but calm expressions, "
        "both heads in frame with headroom, eyelines on upper-third, "
        "Toronto Victorian semi kitchen, soft natural window light from the left"
    )


def build_all_prompts(manifest: dict) -> list:
    """Build prompts for all H2 sections. Returns list of dicts."""
    results = []
    for section in manifest.get("h2_sections", []):
        results.append({
            "section_number": section.get("section_number"),
            "text":           section.get("text", ""),
            "filename":       section.get("filename", ""),
            "is_bottom_line": section.get("is_bottom_line", False),
            "is_faq":         section.get("is_faq", False),
            "prompt":         build_article_prompt(section),
        })
    return results
