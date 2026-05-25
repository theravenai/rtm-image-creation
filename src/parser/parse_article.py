"""
parse_article.py — Blog article parser for AskRoss.ca blog image creation pipeline.

Supports two input formats:
  - HTML / WordPress block format (.txt)
  - Markdown format (.md)

Produces a JSON manifest for downstream image-creation agents.
"""

import json
import math
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GMB_LOCATIONS = ["Toronto", "Ottawa", "Richmond Hill", "Mississauga"]

# Approximate characters per line at 580px wide, 24px font, ~12px avg char width
CHARS_PER_LINE = 48


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert a title string to a lowercase-hyphenated slug."""
    text = text.lower()
    # Remove characters that are not alphanumeric, spaces, or hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def sanitize_filename(h2_text: str, index: int = None) -> str:
    """Sanitize an H2 heading for use in a filename.

    Format: AskRoss.ca - {index} - {text}.png
    The index is the 1-based position of the section in the article.
    """
    text = h2_text.rstrip("?!")
    text = text.replace(": ", "_ ")
    for ch in ['"', "*", "/", "\\", "<", ">"]:
        text = text.replace(ch, "")
    if index is not None:
        return f"AskRoss.ca - {index} - {text}.png"
    return f"AskRoss.ca - {text}.png"


def count_title_lines(title: str) -> int:
    """Estimate how many lines the title wraps to at ~580px / 24px font."""
    line_count = math.ceil(len(title) / CHARS_PER_LINE)
    # Clamp: we only distinguish 2 vs 3 (default 2)
    if line_count >= 3:
        return 3
    return 2


def strip_bold_markers(text: str) -> str:
    """Remove leading/trailing ** markdown bold markers from a string."""
    return re.sub(r"^\*\*|\*\*$", "", text.strip()).strip()


def clean_html_text(text: str) -> str:
    """Strip all HTML tags and decode common entities from a string."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&#8220;", '"').replace("&#8221;", '"')
    return text.strip()


# ---------------------------------------------------------------------------
# Prompt-hint generator
# ---------------------------------------------------------------------------

def generate_prompt_hint(h2_text: str) -> str:
    """Return a literal, concrete 1-sentence photorealistic image description
    based on the H2 topic. Canadian setting, no abstract metaphors."""

    lower = h2_text.lower()

    # --- FAQ / Bottom-line catch-alls (check first) ---
    if "list of all faqs" in lower or ("faq" in lower and "list" in lower):
        return (
            "A clean split-screen infographic showing common mortgage questions on one side "
            "and concise answers on the other, Canadian flag subtly visible in the background."
        )
    if "bottom line" in lower:
        return (
            "A confident Canadian mortgage broker shaking hands with a relieved homeowner couple "
            "across a desk covered in paperwork, bright office lighting, optimistic atmosphere."
        )
    if "advice from ross taylor" in lower:
        return (
            "A friendly Canadian mortgage advisor speaking directly to the camera in a modern "
            "Toronto office, notepad and laptop open, warm professional lighting."
        )

    # --- Specific section topics (HTML article — Bank of Canada rate hold) ---
    if "global events" in lower and "mortgage rates" in lower:
        return (
            "A split image showing Middle East oil rigs and a Toronto skyline with a mortgage "
            "rate chart overlaid, conveying how international events ripple into Canadian borrowing costs."
        )
    if "signal lower rates" in lower or "signal" in lower and "rates are coming" in lower:
        return (
            "A Bank of Canada press conference podium with a blurred spokesperson, a 'rates on hold' "
            "graphic on a screen behind them, cautious expressions in the foreground audience."
        )
    if "could rates still go higher" in lower or ("rates" in lower and "higher" in lower and "year" in lower):
        return (
            "A Canadian homeowner staring at a rising interest-rate graph on a laptop screen, "
            "a worried expression, kitchen table setting with mortgage documents spread out."
        )
    if "what happens to your mortgage right now" in lower:
        return (
            "A Canadian couple reviewing their mortgage statement at a kitchen table, one partner "
            "pointing at a line item with a concerned look, calculator and paperwork visible."
        )
    if "why are fixed rates still going up" in lower or ("fixed rates" in lower and "going up" in lower):
        return (
            "A close-up of a Canadian bond yield chart on a trading screen trending upward, "
            "a newspaper headline reading 'Fixed Rates Rise Again' partially visible beside it."
        )
    if "renew now or wait" in lower or ("renew" in lower and "wait" in lower):
        return (
            "A Canadian homeowner at a desk holding two printed mortgage renewal quotes and "
            "comparing them, a calendar on the wall showing renewal month circled in red."
        )
    if "spring home buyers" in lower or ("spring" in lower and "buyers" in lower):
        return (
            "A Canadian real estate agent pointing at a 'For Sale' sign in front of a suburban home "
            "in spring bloom, a buyer couple attentively listening, clipboard in hand."
        )
    if "prices actually dropping" in lower or ("prices" in lower and ("toronto" in lower or "vancouver" in lower)):
        return (
            "A Toronto condo tower with a price-reduction banner on a real estate listing board "
            "in the foreground, a slightly empty open-house sign visible, overcast sky."
        )
    if "spring market overall" in lower:
        return (
            "A busy but calm Canadian open house — a handful of buyers walking through a well-lit "
            "suburban home, a realtor greeting them at the door, spring sunlight through large windows."
        )
    if "what should canadians actually do" in lower or ("canadians" in lower and "do right now" in lower):
        return (
            "A Canadian family sitting around a kitchen table with a mortgage professional, "
            "reviewing a printed financial plan together, serious but hopeful expressions."
        )

    # --- Specific section topics (Markdown article — sell your home) ---
    if "what is actually happening to canadian homeowners" in lower or (
        "happening" in lower and "homeowners" in lower
    ):
        return (
            "A montage of a declining home-price chart, a worried Canadian family, and a stack "
            "of renewal notices on a kitchen counter, muted newsprint colour palette."
        )
    if "mortgage renewals making this worse" in lower or (
        "renewals" in lower and ("worse" in lower or "renewal" in lower)
    ):
        return (
            "A kitchen table covered in stacked bills and a calendar with a renewal date circled "
            "in red, a Canadian couple looking worried, overhead lighting casting shadows."
        )
    if "equity disappears" in lower or ("equity" in lower and "disappear" in lower):
        return (
            "A model house sinking into a pile of sand, an empty piggy bank beside it, "
            "muted tones suggesting financial loss, neutral studio background."
        )
    if "warning signs" in lower and ("forced sale" in lower or "heading toward" in lower):
        return (
            "A visibly stressed Canadian homeowner holding an overdue mortgage notice, "
            "red warning flags visible in the background, serious and urgent expression."
        )
    if "waiting for the market to recover" in lower or (
        "waiting" in lower and ("recover" in lower or "risky" in lower)
    ):
        return (
            "A calendar with months being crossed off while a home-price chart stays flat, "
            "a Canadian homeowner sitting on a couch looking at phone bills accumulating on the coffee table."
        )
    if "selling your home actually affect your credit" in lower or (
        "selling" in lower and "credit" in lower
    ):
        return (
            "A clean credit score meter jumping from the red zone to green after a successful "
            "home sale, a Canadian homeowner's relieved face reflected in a laptop screen."
        )
    if "financial reset" in lower:
        return (
            "A clean modern desk with a fresh notepad, a sunrise through a window, "
            "a Canadian couple reviewing a new budget plan with an optimistic fresh-start mood."
        )

    # --- Fallback: generic Canadian mortgage/homeowner scene ---
    return (
        f"A photorealistic Canadian homeowner scene illustrating the concept of '{h2_text}', "
        "professional lighting, suburban or urban Toronto setting."
    )


# ---------------------------------------------------------------------------
# HTML / WordPress parser
# ---------------------------------------------------------------------------

def parse_html_article(content: str) -> dict:
    """Parse a WordPress-exported HTML article (.txt) and return a manifest dict."""

    # --- Extract H1 title ---
    # The WP export in our sample has a malformed H1 tag where the id attribute
    # is never closed with a quote, and the title text is inside the id value:
    #
    #   <h1 class="wp-block-heading" id="Why Are Global Events...?</h1>
    #
    # The id value therefore runs: "Why Are Global Events...?</h1>
    # We match it with a pattern that captures from the opening " up to </h1>.

    title = ""

    # Strategy 1: malformed id — value runs all the way to </h1>
    malformed_id_match = re.search(
        r'<h1[^>]*\bid="([^"<]+?)(?:</h1>|")',
        content, re.IGNORECASE
    )
    if malformed_id_match:
        candidate = malformed_id_match.group(1).strip()
        if len(candidate) > 10:
            title = candidate

    # Strategy 2: well-formed H1 — inner text between tags
    if not title:
        inner_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        if inner_match:
            title = clean_html_text(inner_match.group(1)).strip()

    if not title:
        raise ValueError("H1 title not found in HTML article.")

    # --- Find the "Jump to a specific section" H3 ---
    # Everything after this marker is the real content; H2s before it are skipped.
    jump_marker_match = re.search(
        r'<h3[^>]*>.*?Jump to a specific section.*?</h3>',
        content, re.IGNORECASE | re.DOTALL
    )
    if not jump_marker_match:
        raise ValueError("'Jump to a specific section' H3 block not found.")
    jump_end_pos = jump_marker_match.end()

    # Collect the section IDs listed in the jump-to navigation <ul>
    # These <a href="#N"> links tell us which figure IDs are real sections
    nav_block_match = re.search(
        r'<ul[^>]*>(.*?)</ul>',
        content[jump_end_pos:], re.DOTALL | re.IGNORECASE
    )
    nav_section_ids = []
    if nav_block_match:
        nav_section_ids = [int(m) for m in re.findall(r'href="#(\d+)"', nav_block_match.group(1))]

    # --- Find all <figure id="N"> + following <h2> pairs after the jump marker ---
    # Pattern: <figure ... id="N">...</figure> immediately before an <h2>
    figure_h2_pattern = re.compile(
        r'<figure[^>]*\bid="(\d+)"[^>]*>.*?</figure>\s*'
        r'(?:<!--[^>]*?-->\s*)*'  # optional WP block comments between figure and h2
        r'<h2[^>]*>(.*?)</h2>',
        re.IGNORECASE | re.DOTALL
    )

    h2_sections = []
    for m in figure_h2_pattern.finditer(content, jump_end_pos):
        fig_id = int(m.group(1))
        raw_h2 = m.group(2)
        h2_text = clean_html_text(raw_h2)
        h2_text = strip_bold_markers(h2_text)

        is_bottom_line = bool(
            re.search(r"bottom line", h2_text, re.IGNORECASE)
            or re.search(r"advice from ross taylor", h2_text, re.IGNORECASE)
        )
        is_faq = bool(
            re.search(r"\bfaq\b", h2_text, re.IGNORECASE)
            or re.search(r"list of all faqs", h2_text, re.IGNORECASE)
        )

        h2_sections.append({
            "text": h2_text,
            "section_number": fig_id,
            "filename": None,  # assigned after filtering with 1-based index
            "is_bottom_line": is_bottom_line,
            "is_faq": is_faq,
            "prompt_hint": generate_prompt_hint(h2_text),
        })

    if nav_section_ids:
        h2_sections = [s for s in h2_sections if s["section_number"] in nav_section_ids]

    # Assign 1-based sequential filenames after filtering
    for i, section in enumerate(h2_sections, start=1):
        section["filename"] = sanitize_filename(section["text"], index=i)

    return {
        "title": title,
        "slug": slugify(title),
        "title_line_count": count_title_lines(title),
        "gmb_locations": GMB_LOCATIONS,
        "h2_sections": h2_sections,
    }


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def parse_markdown_article(content: str) -> dict:
    """Parse a Markdown-format blog article and return a manifest dict."""

    lines = content.splitlines()

    # --- Extract H1 ---
    title = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = strip_bold_markers(stripped[2:].strip())
            break
    if not title:
        raise ValueError("H1 title not found in Markdown article.")

    # --- Find the "Jump to a specific section" line ---
    jump_line_idx = None
    for i, line in enumerate(lines):
        if re.search(r"Jump to a specific section", line, re.IGNORECASE):
            jump_line_idx = i
            break
    if jump_line_idx is None:
        raise ValueError("'Jump to a specific section' not found in Markdown article.")

    # --- Find the H2 immediately after H1 (subtitle) — we skip it ---
    # It is the first ## line before the jump marker.
    subtitle_text = None
    for line in lines[1:jump_line_idx]:
        stripped = line.strip()
        if stripped.startswith("## "):
            subtitle_text = stripped[3:].strip()
            break

    # --- Collect H2s that appear AFTER the jump marker ---
    # Also stop at the "Metadata Elements" H2 (if present).
    h2_sections = []
    section_counter = 2  # markdown sections start numbering at 2
    image_index = 1      # 1-based sequential index for filenames

    for line in lines[jump_line_idx + 1:]:
        stripped = line.strip()

        if stripped.startswith("## "):
            raw_h2 = stripped[3:].strip()
            h2_text = strip_bold_markers(raw_h2)

            # Stop at metadata section
            if re.search(r"metadata elements", h2_text, re.IGNORECASE):
                break

            is_bottom_line = bool(
                re.search(r"bottom line", h2_text, re.IGNORECASE)
                or re.search(r"advice from ross taylor", h2_text, re.IGNORECASE)
            )
            is_faq = bool(
                re.search(r"\bfaq\b", h2_text, re.IGNORECASE)
                or re.search(r"list of all faqs", h2_text, re.IGNORECASE)
            )

            h2_sections.append({
                "text": h2_text,
                "section_number": section_counter,
                "filename": sanitize_filename(h2_text, index=image_index),
                "is_bottom_line": is_bottom_line,
                "is_faq": is_faq,
                "prompt_hint": generate_prompt_hint(h2_text),
            })
            section_counter += 1
            image_index += 1

    return {
        "title": title,
        "slug": slugify(title),
        "title_line_count": count_title_lines(title),
        "gmb_locations": GMB_LOCATIONS,
        "h2_sections": h2_sections,
    }


# ---------------------------------------------------------------------------
# Auto-detect format and dispatch
# ---------------------------------------------------------------------------

def parse_article(file_path: str) -> dict:
    """Parse a blog article file (HTML or Markdown) and return a manifest dict.

    Args:
        file_path: Absolute path to the article file.

    Returns:
        A dict conforming to the manifest schema.
    """
    path = Path(file_path)
    content = path.read_text(encoding="utf-8", errors="replace")

    ext = path.suffix.lower()
    if ext in (".md", ".markdown"):
        return parse_markdown_article(content)
    else:
        # Default: treat as HTML / WordPress block format
        return parse_html_article(content)


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------

def validate_html_manifest(manifest: dict) -> None:
    """Run post-parse assertions on the HTML test article manifest."""
    expected_title = "Why Are Global Events Driving the Bank of Canada Rate Hold?"
    assert manifest["title"] == expected_title, (
        f"Title mismatch.\n  Got:      {manifest['title']!r}\n  Expected: {expected_title!r}"
    )

    n = len(manifest["h2_sections"])
    assert n == 12, f"Expected 12 h2_sections, got {n}."

    expected_ids = {2, 4, 6, 7, 9, 11, 13, 14, 15, 16, 17, 18}
    actual_ids = {s["section_number"] for s in manifest["h2_sections"]}
    assert actual_ids == expected_ids, (
        f"Section number mismatch.\n  Got:      {sorted(actual_ids)}\n"
        f"  Expected: {sorted(expected_ids)}"
    )

    last = manifest["h2_sections"][-1]
    assert last["is_faq"], f"Last section should be is_faq=True, got: {last}"

    second_last = manifest["h2_sections"][-2]
    assert second_last["is_bottom_line"], (
        f"Second-to-last section should be is_bottom_line=True, got: {second_last}"
    )

    print("  [PASS] HTML manifest validation passed.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    base = Path(__file__).resolve().parent.parent.parent
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)

    # --- Test article (HTML) ---
    html_path = (
        base
        / "(1) Complete Blog Article Images Sample"
        / "Why Are Global Events Driving the Bank of Canada Rate Hold.txt"
    )
    print(f"Parsing HTML article: {html_path.name}")
    html_manifest = parse_article(str(html_path))

    print(f"  Title        : {html_manifest['title']}")
    print(f"  Sections     : {len(html_manifest['h2_sections'])}")
    print(f"  Title lines  : {html_manifest['title_line_count']}")
    print(f"  Slug         : {html_manifest['slug']}")
    print("Validating HTML manifest...")
    validate_html_manifest(html_manifest)

    test_manifest_path = out_dir / "test-manifest.json"
    test_manifest_path.write_text(
        json.dumps(html_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"  Saved: {test_manifest_path}")

    # --- New article (Markdown) ---
    md_path = base / "Should You Sell Your Home Before Things Get Worse.md"
    print(f"\nParsing Markdown article: {md_path.name}")
    md_manifest = parse_article(str(md_path))

    print(f"  Title        : {md_manifest['title']}")
    print(f"  Sections     : {len(md_manifest['h2_sections'])}")
    print(f"  Title lines  : {md_manifest['title_line_count']}")
    print(f"  Slug         : {md_manifest['slug']}")

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(md_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"  Saved: {manifest_path}")

    print("\nParser built and tested. Manifests ready.")


if __name__ == "__main__":
    main()
