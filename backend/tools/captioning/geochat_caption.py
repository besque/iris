"""Scene description through GeoChat, same backend as the VQA tool."""

from backend.tools import geochat_backend as gc
from backend.tools.base import Tool, ToolResult

FIXED_CONFIDENCE = 0.7
DEFAULT_PROMPT = "Describe the land cover and the major objects visible in this satellite image."


class GeoChatCaption(Tool):
    name = "caption"
    description = "Describes the scene in a single image"
    input_types = ["single_optical", "single_sar"]

    def run(self, images, query, **params) -> ToolResult:
        image = gc.load_image(images)
        prompt = query.strip() or DEFAULT_PROMPT
        raw = gc._call_geochat(image, prompt)
        return ToolResult(
            text=raw.strip() or "(no description)",
            confidence=FIXED_CONFIDENCE,
            metadata={
                "model": gc.model_name(),
                "params": {"prompt": prompt, **params},
                "confidence_source": "fixed",
                "backend": gc.backend_name(),
            },
        )
