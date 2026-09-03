"""Change analysis for two dates: a classical change map says WHERE, GeoChat
describes each date and the two descriptions say WHAT. Works with no extra model."""

import re

from backend.tools import geochat_backend as gc
from backend.tools.base import Tool, ToolResult
from backend.tools.change.change_map import change_map

DESCRIBE = "Describe the land cover, buildings, roads and vegetation visible in this satellite image."

# words that hint at each land type, used to compare the two descriptions
THEMES = {
    "built-up": ["building", "house", "villa", "residential", "urban", "construction", "structure", "parking"],
    "roads": ["road", "street", "highway", "path"],
    "vegetation": ["tree", "forest", "vegetation", "grass", "field", "farmland", "crop", "green"],
    "water": ["water", "river", "lake", "pond", "sea"],
}


def _count(text: str, words) -> int:
    t = text.lower()
    return sum(len(re.findall(rf"\b{w}\w*", t)) for w in words)


def _theme_in_query(query: str) -> str | None:
    q = query.lower()
    for theme, words in THEMES.items():
        if theme in q or any(w in q for w in words):
            return theme
    return None


class ChangeTool(Tool):
    name = "change"
    description = "Describes what changed between two images of the same area taken at different times"
    input_types = ["bitemporal_pair"]

    def run(self, images, query, **params) -> ToolResult:
        if len(images) != 2:
            raise ValueError("change analysis needs exactly two images")
        img_a, img_b = gc.load_image(images[0]), gc.load_image(images[1])
        if img_b.size != img_a.size:
            img_b = img_b.resize(img_a.size)

        cm = change_map(img_a, img_b)
        desc_a = gc._call_geochat(img_a, DESCRIBE).strip()
        desc_b = gc._call_geochat(img_b, DESCRIBE).strip()

        theme = _theme_in_query(query)
        trend = None
        if theme:
            before, after = _count(desc_a, THEMES[theme]), _count(desc_b, THEMES[theme])
            trend = "increased" if after > before else "decreased" if after < before else "remained unchanged"

        if cm["percent"] < 1.0:
            text = f"Little to no change detected: about {cm['percent']}% of the scene differs between the two dates."
            if theme:
                text += f" The {theme} appears to have remained unchanged."
        else:
            text = (f"About {cm['percent']}% of the scene changed, concentrated in the {cm['region']}. "
                    f"Earlier image: {desc_a} Later image: {desc_b}")
            if theme and trend:
                text += f" Based on the two descriptions, the {theme} has {trend}."

        descs_differ = _count(desc_a, sum(THEMES.values(), [])) != _count(desc_b, sum(THEMES.values(), []))
        agree = (cm["percent"] >= 1.0) == descs_differ
        return ToolResult(
            text=text,
            spatial={"type": "mask", "data": cm["mask"].astype("uint8")},
            confidence=0.7 if agree else 0.5,
            metadata={
                "model": f"pixel-diff + {gc.model_name()}",
                "params": {"diff_threshold": cm["threshold"], "describe_prompt": DESCRIBE},
                "percent_changed": cm["percent"],
                "region": cm["region"],
                "description_before": desc_a,
                "description_after": desc_b,
                "trend": trend,
                "confidence_source": "map/description agreement",
            },
        )
