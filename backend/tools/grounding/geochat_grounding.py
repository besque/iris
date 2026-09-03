"""Puts a box on the thing the user asked about, through GeoChat's [refer] task.
Box text is parsed into pixel coords by box_parser.py."""

from backend.tools import geochat_backend as gc
from backend.tools.base import Tool, ToolResult
from backend.tools.grounding.box_parser import parse_boxes, strip_boxes

FIXED_CONFIDENCE = 0.7
TAGS = ("[refer]", "[grounding]", "[identify]")


def object_phrase(query: str) -> str:
    """'highlight the water body' -> 'the water body'."""
    q = query.strip().rstrip("?.!")
    lowered = q.lower()
    for verb in ("highlight", "mark", "locate", "find", "show me", "show", "point out", "outline",
                 "draw a box around", "where is", "where are"):
        if lowered.startswith(verb):
            q = q[len(verb):].strip()
            break
    return q


def build_prompt(query: str, task_tag: str = "refer") -> str:
    q = query.strip()
    if q.lower().startswith(TAGS):
        return q
    # GeoChat's referring template. "where is X?" gets prose back, this gets a box
    return f"[{task_tag}] give me the location of {object_phrase(q)}"


def retry_prompt(query: str, task_tag: str = "refer") -> str:
    return f"[{task_tag}] where is {object_phrase(query)}? give me its bounding box"


class GeoChatGrounding(Tool):
    name = "grounding"
    description = "Finds the region in the image that matches the query"
    input_types = ["single_optical", "single_sar"]

    def run(self, images, query, **params) -> ToolResult:
        image = gc.load_image(images)
        width, height = image.size
        task_tag = params.get("task_tag", "refer")
        scale = params.get("coord_scale", gc.coord_scale())
        prompt = build_prompt(query, task_tag)

        meta = {
            "model": gc.model_name(),
            "confidence_source": "fixed",
            "backend": gc.backend_name(),
            "image_size": [width, height],
        }

        # the model boxes something for any [refer] prompt, even on a scene
        # with no such object, so ask first whether it is there at all
        obj = object_phrase(query)
        if params.get("presence_check", True) and not query.strip().lower().startswith(TAGS):
            presence_prompt = f"Is there {obj} in this image? Answer yes or no."
            presence = gc._call_geochat(image, presence_prompt).strip()
            meta["presence_answer"] = presence
            if presence.lower().startswith("no"):
                return ToolResult(
                    text=f"No {obj.removeprefix('the ').removeprefix('a ')} found in the image.",
                    spatial={"type": "bbox", "data": []},
                    confidence=FIXED_CONFIDENCE,
                    metadata={**meta, "raw_output": presence,
                              "params": {"prompts": [presence_prompt], "task_tag": task_tag,
                                         "coord_scale": scale, **params}},
                )

        raw = gc._call_geochat(image, prompt)
        boxes = parse_boxes(raw, width, height, scale)
        attempts = [prompt]
        if not boxes and not query.strip().lower().startswith(TAGS):
            prompt = retry_prompt(query, task_tag)
            attempts.append(prompt)
            raw2 = gc._call_geochat(image, prompt)
            boxes = parse_boxes(raw2, width, height, scale)
            if boxes:
                raw = raw2
        text = strip_boxes(raw)
        if boxes:
            text = text or f"Found {len(boxes)} region(s)."
        else:
            text = (text + " " if text else "") + "No region found."

        return ToolResult(
            text=text.strip(),
            spatial={"type": "bbox", "data": boxes},
            confidence=FIXED_CONFIDENCE if boxes else 0.3,
            metadata={
                **meta,
                "params": {"prompts": attempts, "task_tag": task_tag, "coord_scale": scale, **params},
                "raw_output": raw,
            },
        )
