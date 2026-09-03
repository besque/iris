"""Scene description through GeoChat. Same model as VQA, fixed prompt."""

from backend.tools import geochat_backend as gc
from backend.tools.base import Tool, ToolResult
from backend.tools.vqa.geochat_vqa import FIXED_CONFIDENCE

DEFAULT_PROMPT = "Describe this satellite image in detail."


class GeoChatCaption(Tool):
    name = "caption"
    description = "Describes the scene in a single image"
    input_types = ["single_optical", "single_sar"]

    def run(self, images, query, **params) -> ToolResult:
        image = gc.load_image(images)
        prompt = params.pop("prompt", None) or DEFAULT_PROMPT
        raw = gc._call_geochat(image, prompt)
        return ToolResult(
            text=raw.strip() or "(no answer)",
            confidence=FIXED_CONFIDENCE,
            metadata={
                "model": gc.model_name(),
                "params": {"prompt": prompt, "query": query, **params},
                "confidence_source": "fixed",
                "backend": gc.backend_name(),
                "image_size": list(image.size),
            },
        )
