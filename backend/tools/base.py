"""Common interface every specialist tool must follow.

The agent controller only knows this interface — it never imports a
specific model directly. To add a new tool: subclass Tool, implement
run(), and register it in the registry (backend/agent/registry.py).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    """What every tool returns."""
    text: str                       # the textual answer
    spatial: dict | None = None     # optional: boxes/masks/heatmaps
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)  # model name, params used, etc.


class Tool(ABC):
    """Base class for all specialist tools (VQA, captioning, grounding, ...)."""

    name: str = "base"
    description: str = ""           # the controller reads this to decide when to use the tool
    input_types: list[str] = []     # e.g. ["single_optical"], ["bitemporal_pair"]

    @abstractmethod
    def run(self, images: list, query: str, **params) -> ToolResult:
        """Run the tool on validated image(s) and a query."""
        raise NotImplementedError
