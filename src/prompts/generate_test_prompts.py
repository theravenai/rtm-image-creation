"""
generate_test_prompts.py
------------------------
Loads out/test-manifest.json, runs build_all_prompts() and build_feature_prompt(),
verifies all constraints, and saves out/test-prompts.json.

Run from the repo root:
    python -m src.prompts.generate_test_prompts
"""

import json
import sys
import os

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

sys.path.insert(0, _ROOT)

from src.prompts.prompt_builder import build_all_prompts
from src.prompts.feature_prompt_builder import build_feature_prompt

# ---------------------------------------------------------------------------
# Verification constants
# ---------------------------------------------------------------------------
REQUIRED_PHRASE = "no logos, no signs, no readable text"
CANADIAN_MARKERS = [
    "toronto", "roncesvalles", "cabbagetown", "leslieville", "trinity bellwoods",
    "cn tower", "bank of canada", "ottawa", "montreal", "vancouver", "calgary",
    "victoria", "halifax", "quebec", "canadian", "victorian semi", "maple",
    "craftsman", "duplex", "prairie", "spring blossom", "cherry blossom",
    "parliamentary", "federal architecture", "limestone",
]

ARTICLE_MIN_WORDS = 70
ARTICLE_MAX_WORDS = 110
FEATURE_MIN_WORDS = 70
FEATURE_MAX_WORDS = 140   # feature prompts carry extra crop-guidance text


def _word_count(text: str) -> int:
    return len(text.split())


def _has_canadian_marker(prompt: str) -> bool:
    pl = prompt.lower()
    return any(m in pl for m in CANADIAN_MARKERS)


def _has_required_phrase(prompt: str) -> bool:
    return REQUIRED_PHRASE in prompt


def _has_negatives(prompt: str) -> bool:
    return "avoiding" in prompt.lower()


def verify_article(entry: dict) -> list:
    """Return list of violation strings (empty list = pass)."""
    violations = []
    label = f"S{entry['section_number']}: {entry['text'][:55]}"

    if entry["is_bottom_line"] or entry["is_faq"]:
        if entry["prompt"] is not None:
            violations.append(f"{label} -- bottom_line/faq must have prompt=None")
        return violations

    if entry["prompt"] is None:
        violations.append(f"{label} -- generated section has prompt=None")
        return violations

    wc = _word_count(entry["prompt"])
    if not (ARTICLE_MIN_WORDS <= wc <= ARTICLE_MAX_WORDS):
        violations.append(f"{label} -- word count {wc} outside {ARTICLE_MIN_WORDS}-{ARTICLE_MAX_WORDS}")

    if not _has_required_phrase(entry["prompt"]):
        violations.append(f"{label} -- missing '{REQUIRED_PHRASE}'")

    if not _has_canadian_marker(entry["prompt"]):
        violations.append(f"{label} -- no Canadian marker found")

    if not _has_negatives(entry["prompt"]):
        violations.append(f"{label} -- missing 'avoiding ...' negatives tail")

    return violations


def main():
    manifest_path = os.path.join(_ROOT, "out", "test-manifest.json")
    output_path   = os.path.join(_ROOT, "out", "test-prompts.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Generate article prompts
    results = build_all_prompts(manifest)

    # Generate feature prompt
    feature_prompt = build_feature_prompt(
        title=manifest["title"],
        article_summary=(
            "The Bank of Canada has held its benchmark interest rate amid global economic uncertainty. "
            "This article explains what the rate hold means for Canadian mortgage holders, "
            "home buyers, and the spring real estate market."
        ),
    )

    # Verify article prompts
    all_violations = []
    word_counts = []
    for entry in results:
        vv = verify_article(entry)
        all_violations.extend(vv)
        if entry["prompt"] is not None:
            word_counts.append(_word_count(entry["prompt"]))

    # Verify feature prompt
    fwc = _word_count(feature_prompt)
    if not (FEATURE_MIN_WORDS <= fwc <= FEATURE_MAX_WORDS):
        all_violations.append(
            f"Feature prompt word count {fwc} outside {FEATURE_MIN_WORDS}-{FEATURE_MAX_WORDS}"
        )
    if not _has_canadian_marker(feature_prompt):
        all_violations.append("Feature prompt -- no Canadian marker found")
    if not _has_required_phrase(feature_prompt):
        all_violations.append(f"Feature prompt -- missing '{REQUIRED_PHRASE}'")
    if not _has_negatives(feature_prompt):
        all_violations.append("Feature prompt -- missing 'avoiding ...' negatives tail")

    # Assemble output JSON
    output = {
        "title": manifest["title"],
        "feature_prompt": feature_prompt,
        "feature_prompt_word_count": fwc,
        "article_prompts": results,
        "verification": {
            "violations": all_violations,
            "article_word_count_range": {
                "min": min(word_counts) if word_counts else 0,
                "max": max(word_counts) if word_counts else 0,
            },
            "feature_word_count": fwc,
            "all_pass": len(all_violations) == 0,
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Console report (ASCII-safe)
    sep = "=" * 70
    print("")
    print(sep)
    print("PROMPT GENERATION REPORT")
    print(sep)
    print(f"Article: {manifest['title']}")
    print(f"Sections processed: {len(results)}")
    generated = [r for r in results if r["prompt"] is not None]
    skipped   = [r for r in results if r["prompt"] is None]
    print(f"  Prompts generated : {len(generated)}")
    skip_nums = ", ".join(str(r["section_number"]) for r in skipped)
    print(f"  Skipped (None)    : {len(skipped)} ({skip_nums})")

    if word_counts:
        print(f"\nArticle prompt word counts: {min(word_counts)}-{max(word_counts)} words")
    print(f"Feature prompt word count : {fwc} words")

    print("\n--- PROMPTS ---")
    for r in results:
        flag = " [SKIPPED - reusable image]" if r["prompt"] is None else ""
        print(f"\n[S{r['section_number']}] {r['text']}{flag}")
        if r["prompt"]:
            wc = _word_count(r["prompt"])
            print(f"  ({wc} words)")
            print(f"  {r['prompt']}")

    print(f"\n[FEATURE PROMPT] ({fwc} words)")
    print(f"  {feature_prompt}")

    print("\n--- VERIFICATION ---")
    if all_violations:
        print(f"VIOLATIONS ({len(all_violations)}):")
        for v in all_violations:
            print(f"  FAIL: {v}")
        sys.exit(1)
    else:
        print("All checks passed.")

    print(f"\nOutput saved to: {output_path}")
    print("\nPrompt builder built. Test prompts generated.")


if __name__ == "__main__":
    main()
