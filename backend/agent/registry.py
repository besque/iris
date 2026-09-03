"""Fixed list of tools the controller can pick from."""

TOOL_REGISTRY = {
    # "vqa": "backend.tools.vqa",
    # "caption": "backend.tools.captioning",
    # "grounding": "backend.tools.grounding",
    # "change_vqa": "backend.tools.change",
    # "optical_sar_fusion": "backend.tools.fusion",
}


def get_tool(name: str):
    """Load a tool by name."""
    raise NotImplementedError
