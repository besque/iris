"""Tool registry — the fixed menu of tools the agent can pick from.

The problem statement requires a *predefined registry*: the controller may
only select from these, with permitted parameters. Keep this the single
source of truth for what the system can do.
"""

TOOL_REGISTRY = {
    # name: (import path, description shown to the controller)
    # "vqa": "backend.tools.vqa",
    # "caption": "backend.tools.captioning",
    # "grounding": "backend.tools.grounding",
    # "change_vqa": "backend.tools.change",
    # "optical_sar_fusion": "backend.tools.fusion",
}


def get_tool(name: str):
    """Load and return a tool instance by name."""
    raise NotImplementedError("Wire up once first tools exist")
