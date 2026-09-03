"""Single-image VQA through GeoChat. Swap where the model runs in
backend/tools/geochat_backend.py, nothing here changes."""

from backend.tools import geochat_backend as gc
from backend.tools.base import Tool, ToolResult

FIXED_CONFIDENCE = 0.7   # GeoChat gives no score, so we do not pretend to have one


class GeoChatVQA(Tool):
    name = "vqa"
    description = "Answers questions about a single image"
    input_types = ["single_optical", "single_sar"]

    def run(self, images, query, **params) -> ToolResult:
        image = gc.load_image(images)
        prompt = query.strip()
        raw = gc._call_geochat(image, prompt)
        return ToolResult(
            text=raw.strip() or "(no answer)",
            confidence=FIXED_CONFIDENCE,
            metadata={
                "model": gc.model_name(),
                "params": {"prompt": prompt, **params},
                "confidence_source": "fixed",
                "backend": gc.backend_name(),
                "image_size": list(image.size),
            },
        )
