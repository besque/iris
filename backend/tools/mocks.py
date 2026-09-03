"""Fake tools so the pipeline runs before the real models land.
Delete each one as its real version arrives."""

from backend.tools.base import Tool, ToolResult


class MockVQATool(Tool):
    name = "vqa"
    description = "Answers questions about a single image"
    input_types = ["single_optical", "single_sar"]

    def run(self, images, query, **params):
        return ToolResult(
            text="Mock answer: the image mostly shows agricultural land with a river in the east.",
            confidence=0.8,
            metadata={"model": "mock", "params": params},
        )


class MockCaptionTool(Tool):
    name = "caption"
    description = "Describes the scene in a single image"
    input_types = ["single_optical", "single_sar"]

    def run(self, images, query, **params):
        return ToolResult(
            text="Mock caption: a coastal town with a harbor, dense housing, and surrounding farmland.",
            confidence=0.75,
            metadata={"model": "mock", "params": params},
        )


class MockGroundingTool(Tool):
    name = "grounding"
    description = "Finds the region in the image that matches the query"
    input_types = ["single_optical", "single_sar"]

    def run(self, images, query, **params):
        return ToolResult(
            text="Mock: highlighted the water body in the north-west.",
            spatial={"type": "bbox", "data": [[120, 40, 300, 210]]},
            confidence=0.7,
            metadata={"model": "mock", "params": params},
        )


class MockChangeTool(Tool):
    name = "change"
    description = "Describes what changed between two images of the same area"
    input_types = ["bitemporal_pair"]

    def run(self, images, query, **params):
        return ToolResult(
            text="Mock: built-up area increased in the south, cropland decreased.",
            spatial={"type": "mask", "data": None},
            confidence=0.65,
            metadata={"model": "mock", "params": params},
        )


class MockFusionTool(Tool):
    name = "fusion"
    description = "Combines an optical and a SAR image to find built-up and water regions"
    input_types = ["crossmodal_pair"]

    def run(self, images, query, **params):
        return ToolResult(
            text="Mock: water covers ~12% of the scene, built-up ~30%, per combined optical and SAR.",
            spatial={"type": "mask", "data": None},
            confidence=0.6,
            metadata={"model": "mock", "params": params},
        )
