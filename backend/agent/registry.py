"""Fixed list of tools the controller can pick from."""

from backend.tools.fusion.fusion_tool import FusionTool
from backend.tools.mocks import (
    MockCaptionTool,
    MockChangeTool,
    MockGroundingTool,
    MockVQATool,
)

# swap a mock for the real tool here when it lands, nothing else changes
TOOL_REGISTRY = {
    "vqa": MockVQATool(),            # mock, waiting on person 2
    "caption": MockCaptionTool(),    # mock, waiting on person 2
    "grounding": MockGroundingTool(),  # mock, waiting on person 2
    "change": MockChangeTool(),      # mock, waiting on person 3
    "fusion": FusionTool(),          # real
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
