"""Fixed list of tools the controller can pick from."""

from backend.tools.captioning.geochat_caption import GeoChatCaption
from backend.tools.change.change_tool import ChangeTool
from backend.tools.fusion.fusion_tool import FusionTool
from backend.tools.grounding.geochat_grounding import GeoChatGrounding
from backend.tools.vqa.geochat_vqa import GeoChatVQA

TOOL_REGISTRY = {
    "vqa": GeoChatVQA(),
    "caption": GeoChatCaption(),
    "grounding": GeoChatGrounding(),
    "change": ChangeTool(),
    "fusion": FusionTool(),
}


def get_tool(name: str):
    if name not in TOOL_REGISTRY:
        raise KeyError(f"unknown tool: {name}")
    return TOOL_REGISTRY[name]


def describe_tools() -> str:
    """Tool menu as text, used in the router prompt."""
    lines = []
    for name, tool in TOOL_REGISTRY.items():
        lines.append(f"- {name}: {tool.description} (accepts: {', '.join(tool.input_types)})")
    return "\n".join(lines)
