"""
Ask Ross Newsletter — Sonar Image Builder
Produces a 1200 × 900 px PNG for Google My Business + Facebook.
Uses Perplexity Sonar to find recent news, extracts the hero image
from the top article results (via og:image meta tags).

Usage:
    # Browse candidate images before building
    python build_newsletter_sonar.py --list-images --sonar-query "Mark Carney housing"

    # Build with first result
    python build_newsletter_sonar.py \
        --sonar-query "Mark Carney Canada Prime Minister" \
        --title1 "Mark Carney's Win: What It Means for Housing" \
        --intro "Canada has a new PM and housing is front and center..."

Requires:
    .env with PERPLEXITY_API_KEY=...
    assets/ask-ross-overlay.png
    fonts/Aleo-Regular.ttf, fonts/Aleo-Bold.ttf, fonts/OpenSans-Regular.ttf
"""

import argparse
import json
import os
import re
from io import BytesIO
from pathlib import Path
from textwrap import dedent

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR   = SCRIPT_DIR.parent

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# Sonar search + image extraction
# ---------------------------------------------------------------------------

# Domains Sonar will search and return images from
SEARCH_DOMAINS = [
    "cnn.com", "nytimes.com", "thetimes.co.uk", "globalnews.ca",
    "reuters.com", "apnews.com", "bbc.com", "cbc.ca", "theglobeandmail.com", "ctv.ca",
]


def _sonar_search(
    query: str, api_key: str, recency: str = "month"
) -> tuple[str, list[str], list[dict]]:
    """Run a Perplexity Sonar search with return_images + domain filter.

    Returns (answer_text, citation_urls, image_candidates).
    """
    payload = {
        "model": "sonar",
        "return_images": True,
        "search_recency_filter": recency,
        "search_domain_filter": SEARCH_DOMAINS,
        "return_citations": True,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You find recent editorial news photographs of the requested subject. "
                    "Return only professional landscape photos — no illustrations, "
                    "infographics, charts, screenshots, social media graphics, or logos. "
                    "Prefer 16:9 photos of the subject speaking, at a podium, or at a "
                    "press conference."
                ),
            },
            {
                "role": "user",
                "content": f"Find recent news photographs of {query}. Photographs only.",
            },
        ],
    }
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])

    # Parse images array — Sonar returns list of dicts or strings
    raw_images = data.get("images", [])
    images: list[dict] = []
    for item in raw_images:
        if isinstance(item, str):
            images.append({"image_url": item, "source_url": "", "title": "(Sonar image)"})
        elif isinstance(item, dict):
            url = item.get("url") or item.get("image_url") or item.get("src") or ""
            origin = item.get("origin_url") or item.get("source_url") or ""
            title = item.get("title") or item.get("description") or "(Sonar image)"
            if url:
                images.append({"image_url": url, "source_url": origin, "title": str(title)[:90]})

    return content, citations, images


def _get_og_image(page_url: str) -> tuple[str, str] | None:
    """Fetch a page and return (og_image_url, page_title), or None."""
    try:
        r = requests.get(page_url, timeout=10, headers=HEADERS)
        if r.status_code != 200:
            return None
        html = r.text

        title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        title = title_m.group(1).strip() if title_m else page_url

        for pattern in [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']',
        ]:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                img_url = m.group(1).strip()
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(page_url)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                return img_url, title
    except Exception:
        pass
    return None


def collect_candidates(
    query: str, api_key: str, count: int = 10, recency: str = "month"
) -> list[dict]:
    """Run Sonar and return a list of candidate image dicts."""
    print(f"  Searching Sonar: '{query}' (recency={recency}, domains={len(SEARCH_DOMAINS)})...")
    content, citations, direct_images = _sonar_search(query, api_key, recency)

    candidates: list[dict] = []

    # Primary: images returned directly by Sonar's return_images
    if direct_images:
        print(f"  Sonar returned {len(direct_images)} direct image(s).")
        for img in direct_images[:count]:
            if img["image_url"]:
                candidates.append(img)

    # Secondary: OG images from citation pages (fill up to count)
    remaining = max(0, count - len(candidates))
    if remaining and citations:
        print(f"  Extracting OG images from {min(len(citations), remaining)} citation page(s)...")
        for url in citations[:remaining]:
            result = _get_og_image(url)
            if result:
                img_url, title = result
                candidates.append({
                    "image_url": img_url,
                    "source_url": url,
                    "title": title[:90],
                })

    # Fallback: direct image URLs mentioned in Sonar's response text
    for img_url in re.findall(
        r"https?://[^\s\"'<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s\"'<>]*)?",
        content,
    )[:5]:
        candidates.append({
            "image_url": img_url,
            "source_url": "",
            "title": "(image URL from Sonar response)",
        })

    return candidates


def _download_image(url: str) -> Image.Image:
    r = requests.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")


CACHE_PATH = ROOT_DIR / "out" / "_sonar_candidates_cache.json"


def _save_cache(candidates: list[dict]) -> None:
    os.makedirs(str(ROOT_DIR / "out"), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)


def _load_cache() -> list[dict] | None:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return None


def list_sonar_images(query: str, api_key: str, count: int = 10, recency: str = "month") -> None:
    candidates = collect_candidates(query, api_key, count, recency)
    if not candidates:
        print(f"No images found for '{query}'")
        return
    _save_cache(candidates)
    print(f"\n{len(candidates)} candidate images for '{query}':")
    for i, c in enumerate(candidates):
        try:
            if "ytimg.com" in c["image_url"] or "youtube.com" in c["image_url"]:
                dims = "1280x720"
                status = "YouTube — auto-skipped (baked-in text)"
            else:
                img = _download_image(c["image_url"])
                w, h = img.width, img.height
                ratio = w / h
                dims = f"{w}x{h} ({ratio:.2f})"
                if ratio >= 1.7:
                    status = "16:9 widescreen - good"
                elif ratio >= 1.5:
                    status = "landscape - ok"
                else:
                    status = "PORTRAIT/SQUARE — auto-skipped"
        except Exception:
            dims, status = "?", "could not download"
        print(f"  [{i}] {c['title']}")
        print(f"       {dims}  {status}")
        print(f"       img : {c['image_url']}")
        if c["source_url"]:
            print(f"       page: {c['source_url']}")
    print(f"\nCandidates cached. Run build with --use-cache --image-index N to use this exact list.")
    print()


def fetch_sonar_image(
    query: str,
    api_key: str,
    image_index: int | None = None,
    count: int = 10,
    use_cache: bool = False,
    recency: str = "month",
) -> tuple[Image.Image, dict]:
    if use_cache:
        candidates = _load_cache()
        if not candidates:
            raise RuntimeError("No cached candidates found. Run --list-images first to populate the cache.")
        print(f"  Using cached candidate list ({len(candidates)} items).")
    else:
        candidates = collect_candidates(query, api_key, count, recency)
    if not candidates:
        raise RuntimeError(f"No images found for query: {query!r}")

    if image_index is not None:
        if image_index >= len(candidates):
            raise RuntimeError(
                f"--image-index {image_index} out of range "
                f"({len(candidates)} candidates). Run --list-images to browse."
            )
        c = candidates[image_index]
        print(f"  [{image_index}] {c['title']}")
        print(f"  Downloading: {c['image_url']}")
        img = _download_image(c["image_url"])
        print(f"  Size: {img.width}x{img.height} ({img.width/img.height:.2f})")
        return _crop_to_banner(img), c

    # Auto mode — prefer 16:9 widescreen, accept any landscape, skip portrait/YouTube
    print("  Auto-selecting best landscape image...")
    landscape_fallback: tuple[Image.Image, dict] | None = None
    for i, c in enumerate(candidates):
        img_url = c["image_url"]
        if "ytimg.com" in img_url or "youtube.com" in img_url:
            print(f"  [{i}] YouTube — skipping (baked-in text)")
            continue
        try:
            img = _download_image(img_url)
            w, h = img.width, img.height
            ratio = w / h
            if ratio >= 1.7:
                print(f"  [{i}] {w}x{h} ({ratio:.2f}) 16:9 widescreen — selected: {c['title']}")
                return _crop_to_banner(img), c
            elif ratio >= 1.5:
                print(f"  [{i}] {w}x{h} ({ratio:.2f}) landscape — keeping as fallback: {c['title']}")
                if landscape_fallback is None:
                    landscape_fallback = (_crop_to_banner(img), c)
            else:
                print(f"  [{i}] {w}x{h} ({ratio:.2f}) portrait/square — skipping")
        except Exception as e:
            print(f"  [{i}] download failed ({e}) — skipping")

    if landscape_fallback:
        img, c = landscape_fallback
        print(f"  No 16:9 found — using best landscape fallback: {c['title']}")
        return img, c

    raise RuntimeError(
        "No landscape images found in candidates. "
        "Run --list-images and use --image-index to pick one manually."
    )


def _crop_to_banner(img: Image.Image) -> Image.Image:
    target_w, target_h = 1200, 638
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / src_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


# ---------------------------------------------------------------------------
# Step 1 — blank canvas
# ---------------------------------------------------------------------------

def create_canvas() -> Image.Image:
    return Image.new("RGBA", (1200, 900), (255, 255, 255, 255))


# ---------------------------------------------------------------------------
# Step 3 — composite overlay
# ---------------------------------------------------------------------------

def apply_overlay(canvas: Image.Image) -> Image.Image:
    overlay_path = SCRIPT_DIR / "overlays" / "ask-ross-overlay.png"
    overlay = Image.open(overlay_path).convert("RGBA")
    if overlay.size != (1200, 900):
        overlay = overlay.resize((1200, 900), Image.LANCZOS)
    return Image.alpha_composite(canvas, overlay)


# ---------------------------------------------------------------------------
# Step 4 — draw text
# ---------------------------------------------------------------------------

def _load_font(name: str, size_px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(SCRIPT_DIR / "fonts" / name), size_px)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        bbox = font.getbbox(trial)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _balance_lines(lines: list[str], font: ImageFont.FreeTypeFont) -> list[str]:
    """Shape 3-line intro so line 2 is the longest and line 3 has at least 3 words.

    Step 1 — move words from line 1 to line 2 until line 2 is the widest.
    Step 2 — move words from line 2 to line 3 until line 3 has at least 3 words.
    """
    if len(lines) != 3:
        return lines

    def px(text: str) -> int:
        bb = font.getbbox(text)
        return bb[2] - bb[0]

    # Step 1: make line 2 wider than line 1
    while len(lines[0].split()) > 1 and px(lines[0]) >= px(lines[1]):
        words1 = lines[0].split()
        lines[0] = " ".join(words1[:-1])
        lines[1] = words1[-1] + " " + lines[1]

    # Step 2: line 3 minimum 3 words (not a cap — line 3 may have more)
    words3 = lines[2].split()
    while len(words3) < 3:
        words2 = lines[1].split()
        if len(words2) <= 1:
            break
        lines[1] = " ".join(words2[:-1])
        words3 = [words2[-1]] + words3
    lines[2] = " ".join(words3)

    return lines


def _sanitize_text(text: str) -> str:
    return text.replace("—", " - ").replace("–", " - ")


def draw_text(canvas: Image.Image, title1: str, title2: str, intro: str) -> Image.Image:
    draw = ImageDraw.Draw(canvas)
    f_title1 = _load_font("Aleo-Regular.ttf", 35)
    f_title2 = _load_font("Aleo-Regular.ttf", 35)
    f_intro  = _load_font("OpenSans-Regular.ttf", 27)
    DARK = (26, 26, 26)
    GRAY = (74, 74, 74)

    t1 = _sanitize_text(title1)
    if len(t1) > 55:
        print(f"  WARNING: title1 is {len(t1)} chars (max 55).")
    draw.text((230, 661.72), t1, font=f_title1, fill=DARK)
    draw.text((230, 704.79), _sanitize_text(title2), font=f_title2, fill=DARK)

    intro_clean = _sanitize_text(intro)
    if len(intro_clean) > 245:
        print(f"  WARNING: intro is {len(intro_clean)} chars (max 245). Capped at 3 lines.")
    for i, line in enumerate(_balance_lines(_wrap_text(intro_clean, f_intro, 1010)[:3], f_intro)):
        draw.text((112, 761.44 + i * 40), line, font=f_intro, fill=GRAY)

    return canvas


# ---------------------------------------------------------------------------
# Save + QC
# ---------------------------------------------------------------------------

def save_final(canvas: Image.Image, output_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final = Image.new("RGB", canvas.size, (255, 255, 255))
    final.paste(canvas, mask=canvas.split()[3])
    assert final.size == (1200, 900), f"Size mismatch: {final.size}"
    final.save(output_path, "PNG", optimize=True)


def qc(path: str) -> None:
    img = Image.open(path).convert("RGB")
    assert img.size == (1200, 900), f"Bad size: {img.size}"
    px = img.load()
    assert px[600, 800] == (255, 255, 255), f"White band missing: {px[600, 800]}"
    assert px[600, 300] != (0, 0, 0), "Banner not visible"
    assert px[300, 680] != (255, 255, 255), "TITLE1 not rendered"
    print("  QC passed — white band OK, banner visible, title rendered")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _title_to_filename(title1: str) -> str:
    name = title1.replace(": ", " - ").replace(":", " -")
    for ch in r'\/*?"<>|':
        name = name.replace(ch, "")
    return name.strip()


def _zoom_banner(banner: Image.Image, zoom: float) -> Image.Image:
    tw, th = 1200, 638
    cw, ch = int(tw / zoom), int(th / zoom)
    left = (tw - cw) // 2
    top  = th - ch
    return banner.crop((left, top, left + cw, top + ch)).resize((tw, th), Image.LANCZOS)


# ---------------------------------------------------------------------------
# End-to-end runner
# ---------------------------------------------------------------------------

def build_newsletter(
    sonar_query: str,
    title1: str,
    title2: str,
    intro: str,
    output_path: str | None = None,
    reuse_banner: bool = False,
    banner_zoom: float = 1.0,
    image_index: int | None = None,
    image_count: int = 10,
    use_cache: bool = False,
    recency: str = "month",
) -> None:
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key and not reuse_banner:
        raise RuntimeError("PERPLEXITY_API_KEY not set. Add it to .env.")

    stem = _title_to_filename(title1)
    out_dir = ROOT_DIR / "out"
    os.makedirs(str(out_dir), exist_ok=True)
    if output_path is None:
        output_path = str(out_dir / f"{stem} GMB Share.png")
    banner_path = str(out_dir / f"{stem} Banner.png")
    credits_path = str(out_dir / f"{stem} Credits.txt")

    print("Step 1: Creating canvas...")
    canvas = create_canvas()

    if reuse_banner and Path(banner_path).exists():
        print("Step 2: Loading existing banner (skipping search)...")
        banner = Image.open(banner_path).convert("RGB")
    else:
        print(f"Step 2: Finding image via Sonar...")
        banner, meta = fetch_sonar_image(sonar_query, api_key, image_index, image_count, use_cache, recency)
        banner.save(banner_path, "PNG", optimize=True)
        print(f"  Banner saved: {banner_path}")
        with open(credits_path, "w", encoding="utf-8") as f:
            f.write(f"Article: {meta.get('title', '')}\n")
            f.write(f"Source:  {meta.get('source_url', '')}\n")
            f.write(f"Image:   {meta.get('image_url', '')}\n")
        print(f"  Credits saved: {credits_path}")

    if banner_zoom != 1.0:
        print(f"  Applying {banner_zoom}x zoom (bottom-anchored)...")
        banner = _zoom_banner(banner, banner_zoom)

    canvas.paste(banner, (0, 0))
    print(f"  Banner size: {banner.size}")

    print("Step 3: Applying overlay...")
    canvas = apply_overlay(canvas)

    print("Step 4: Drawing text...")
    canvas = draw_text(canvas, title1, title2, intro)

    print(f"Saving to {output_path}...")
    save_final(canvas, output_path)
    print("Running QC...")
    qc(output_path)
    print(f"\nDone: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv(ROOT_DIR / ".env")

    parser = argparse.ArgumentParser(
        description="Build an Ask Ross Newsletter image using a photo found via Perplexity Sonar.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Examples:
              # Browse candidates first
              python build_newsletter_sonar.py --list-images \\
                --sonar-query "Mark Carney Canada Prime Minister"

              # Build with first result
              python build_newsletter_sonar.py \\
                --sonar-query "Mark Carney Canada Prime Minister" \\
                --title1 "Mark Carney's Win: What It Means for Housing" \\
                --intro "Canada has a new PM and housing is front and center..."

              # Try a different result
              python build_newsletter_sonar.py \\
                --sonar-query "Mark Carney Canada Prime Minister" \\
                --image-index 2 --title1 "..." --intro "..."
        """),
    )
    parser.add_argument("--sonar-query", default="Mark Carney Canada Prime Minister",
                        help="Search query sent to Perplexity Sonar")
    parser.add_argument("--title1",
                        default="Mark Carney's Win: What It Means for Housing")
    parser.add_argument("--title2", default="| Ask Ross Newsletter")
    parser.add_argument("--intro", default=(
        "Canada has a new PM and housing is front and center. From GST breaks for "
        "first-time buyers to 4M new homes by 2035, here's what Carney's win means for you."
    ))
    parser.add_argument("--output", default=None)
    parser.add_argument("--reuse-banner", action="store_true")
    parser.add_argument("--banner-zoom", type=float, default=1.0)
    parser.add_argument("--image-index", type=int, default=None,
                        help="Which candidate to use. Default: auto-pick first landscape image. Run --list-images to browse.")
    parser.add_argument("--image-count", type=int, default=10,
                        help="How many article candidates to search")
    parser.add_argument("--list-images", action="store_true",
                        help="List candidate images, cache them, and exit without building")
    parser.add_argument("--use-cache", action="store_true",
                        help="Use the candidate list saved by the last --list-images run (avoids a new search)")
    parser.add_argument("--recency", default="month",
                        choices=["day", "week", "month", "year"],
                        help="How recent the search results should be (default: month)")

    args = parser.parse_args()

    if args.list_images:
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        if not api_key:
            raise RuntimeError("PERPLEXITY_API_KEY not set.")
        list_sonar_images(args.sonar_query, api_key, args.image_count, args.recency)
        return

    build_newsletter(
        sonar_query=args.sonar_query,
        title1=args.title1,
        title2=args.title2,
        intro=args.intro,
        output_path=args.output,
        reuse_banner=args.reuse_banner,
        banner_zoom=args.banner_zoom,
        image_index=args.image_index,
        image_count=args.image_count,
        use_cache=args.use_cache,
        recency=args.recency,
    )


if __name__ == "__main__":
    main()
