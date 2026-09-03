"""Turns per-tool confidences into one top-level score."""

from backend.tools.base import ToolResult


def aggregate_confidence(results: list[ToolResult]) -> float:
    """Weakest link wins. Missing confidences count as 0.5."""
    if not results:
        return 0.0
    return min(r.confidence if r.confidence is not None else 0.5 for r in results)
