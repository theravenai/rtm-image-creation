"""
feature_prompt_builder.py
-------------------------
Builds the ONE shared background image prompt for AskRoss.ca feature image,
desktop banner, mobile banner, and GMB posts.

Crops: 700x450 feature, 1286x300 banner, 400x600 mobile, 1200x900 GMB.
Master: 1920x1080 with subject vertically centered.
Target length: 70-140 words.
"""

import re
from .prompt_builder import NEGATIVES


def build_feature_prompt(title: str, article_summary: str = "") -> str:
    """
    Generate the ONE background image prompt for the feature/banner/GMB
    shared background.

    Subject is vertically centered so all crop ratios capture it.
    Upper-left ~260x100px kept quiet for logo overlay.
    No readable text, logos, or signs.
    """
    combined = (title + " " + article_summary).lower()

    if any(w in combined for w in ["sell", "forced sale", "equity loss", "negative equity"]):
        scene = (
            "Medium shot of a mid-40s Canadian homeowner couple on the porch of a "
            "Roncesvalles Victorian semi, looking at the street with worried uncertain expressions, "
            "both heads in frame with headroom, eyelines at the vertical midline"
        )
        canadian = "autumn maple trees in amber and gold lining the residential street"
        lighting = "soft overcast autumn afternoon light, cool muted palette"
        mood = "mood cautionary and weighted, heavy contemplative atmosphere"

    elif any(w in combined for w in ["bank of canada", "rate hold", "global events", "mortgage rate"]):
        scene = (
            "Wide shot of the Bank of Canada limestone headquarters in Ottawa, "
            "facade filling the lower half of the frame, "
            "center of mass at the vertical midline, Canadian flag on a left-edge pole"
        )
        canadian = "Bank of Canada Ottawa limestone facade, federal-precinct setting"
        lighting = "soft overcast morning light, cool grey sky at most top 30 percent of frame"
        mood = "mood grounded and observational with cautious undercurrent, neutral editorial tone"

    elif any(w in combined for w in ["spring", "buy", "buyers", "opportunity", "fresh start"]):
        scene = (
            "Medium wide shot of a young Canadian couple with a real estate agent "
            "in front of a Cabbagetown Victorian semi in spring bloom, "
            "all three heads in frame with headroom, eyelines at the vertical midline"
        )
        canadian = "Cabbagetown Toronto sidewalk with spring cherry blossoms"
        lighting = "bright soft spring daylight, slightly overcast, warm neutral palette"
        mood = "mood quietly optimistic and open, soft spring energy"

    else:
        scene = (
            "Medium shot of a Canadian homeowner couple in autumn coats walking on a "
            "Roncesvalles sidewalk, mid-conversation with serious calm expressions, "
            "both heads in frame with headroom, eyelines at the vertical midline"
        )
        canadian = "Roncesvalles Victorian semis and autumn maples in full orange and gold"
        lighting = "soft overcast late-afternoon light, warm neutral colour temperature"
        mood = "mood quietly contemplative and measured, grounded editorial tone"

    extra_negatives = (
        "subject at vertical extremes, vast empty sky, "
        "subject too small for portrait crop"
    )
    all_negatives = NEGATIVES + ", " + extra_negatives

    prompt = (
        f"{scene}, {canadian}, {lighting}, {mood}, "
        f"subject vertically centered for multi-ratio cropping, "
        f"upper-left kept as plain sky or soft blurred foliage for logo overlay, "
        f"1920x1080 16:9 wide aspect master, photorealistic editorial photography, "
        f"avoiding {all_negatives}."
    )

    prompt = re.sub(r" {2,}", " ", prompt)
    prompt = re.sub(r",{2,}", ",", prompt)
    return prompt.strip()
