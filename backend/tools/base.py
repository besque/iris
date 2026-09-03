"""Base interface every tool follows.
New tool: subclass Tool, implement run(), add it to the registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    text: str
    spatial: dict | None = None     # boxes, masks, heatmaps
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)


class Tool(ABC):
    name: str = "base"
    description: str = ""
    input_types: list[str] = []     # e.g. ["single_optical"], ["bitemporal_pair"]

    @abstractmethod
    def run(self, images: list, query: str, **params) -> ToolResult:
        raise NotImplementedError
