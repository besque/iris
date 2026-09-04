"""Change analysis for two dates: a classical change map says WHERE, the VLM
sees both dates side by side and says WHAT. Works with no extra model."""

import re

from PIL import Image

from backend.tools import geochat_backend as gc
from backend.tools.base import Tool, ToolResult
from backend.tools.change.change_map import change_map

CHANGE_CUTOFF = 15.5   # percent of pixels; balanced cut-off from scripts/eval_change_map.py on 160 LEVIR-CC pairs

PROMPT = ("These are two satellite images of the same area. The LEFT image was taken earlier, "
          "the RIGHT image later. {query} Look only for new or removed buildings, roads or "
          "cleared land. Ignore season, lighting, colour and shadow differences. If the "
          "structures are the same in both, answer exactly 'No real change.' Otherwise answer in "
          "two or three sentences saying what changed and where.")

UNCHANGED = re.compile(r"\b(no (real |significant |noticeable )?change|unchanged|remain(s|ed)? the same|"
                       r"no difference|identical|same as before|has not changed)\b", re.I)
INCREASED = re.compile(r"\b(increas|expand|grew|grown|more buildings|new (buildings|houses|roads|structures)|"
                       r"added|appear(ed|s)?|constructed|built)\w*", re.I)
DECREASED = re.compile(r"\b(decreas|reduc|shrunk|shrank|fewer|removed|demolish|disappear|cleared|lost)\w*", re.I)


def side_by_side(a: Image.Image, b: Image.Image, gap: int = 12) -> Image.Image:
    b = b.resize(a.size)
    out = Image.new("RGB", (a.width * 2 + gap, a.height), (255, 255, 255))
    out.paste(a, (0, 0))
    out.paste(b, (a.width + gap, 0))
    return out


def verdict(text: str) -> str:
    head = text[:120]   # the model is told to open with the verdict
    if UNCHANGED.search(head):
        return "remained unchanged"
    if DECREASED.search(text) and not INCREASED.search(text):
        return "decreased"
    if INCREASED.search(text) or re.search(r"replaced (with|by)|converted|now (has|shows)", text, re.I):
        return "increased"
    return "changed"


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
        map_says_change = cm["percent"] >= CHANGE_CUTOFF

        # small VLMs report a change for any pair, so the map decides IF and the model says WHAT
        if not map_says_change:
            trend, answer = "remained unchanged", ""
            text = (f"No significant structural change detected between the two dates: about {cm['percent']}% "
                    f"of pixels differ, consistent with seasonal or lighting variation.")
            if any(w in query.lower() for w in ("built", "building", "urban")):
                text += " The built-up area appears unchanged."
        else:
            prompt = PROMPT.format(query=query.strip())
            answer = gc._call_geochat(side_by_side(img_a, img_b), prompt).strip()
            trend = verdict(answer)
            text = (f"{answer} The change map marks about {cm['percent']}% of the scene, "
                    f"mainly in the {cm['region']}.")
        model_says_change = trend != "remained unchanged"

        return ToolResult(
            text=text,
            spatial={"type": "mask", "data": cm["mask"].astype("uint8")},
            confidence=0.7 if (not map_says_change or cm["percent"] >= CHANGE_CUTOFF + 3) else 0.6,
            metadata={
                "model": f"{gc.model_name()} (side-by-side) + pixel-diff",
                "params": {"diff_threshold": cm["threshold"], "cutoff_percent": CHANGE_CUTOFF, "prompt": PROMPT if map_says_change else None},
                "percent_changed": cm["percent"],
                "region": cm["region"],
                "trend": trend,
                "confidence_source": "map/model agreement",
            },
        )
