"""Reads the query, picks tools, runs them, collects the trace."""

import json
import os

from backend.agent.confidence import aggregate_confidence
from backend.agent.registry import TOOL_REGISTRY, describe_tools, get_tool

# stand-in until the real validator lands, then delete
FAKE_VALIDATED_INPUTS = {
    "config_type": "single_optical",
    "images": ["data/samples/fake.png"],
    "warnings": [],
}

# maps whatever the validator emits to our canonical names
CONFIG_ALIASES = {
    "single_optical": "single_optical",
    "single_sar": "single_sar",
    "bitemporal_pair": "bitemporal_pair",
    "crossmodal_pair": "crossmodal_pair",
    # add validator variants here if their names differ, e.g. "optical_sar_pair": "crossmodal_pair"
}


def normalize_input_config(config_type: str) -> str:
    key = config_type.strip().lower()
    if key not in CONFIG_ALIASES:
        raise ValueError(f"unknown input config: {config_type}")
    return CONFIG_ALIASES[key]


def rule_route(query: str, config: str) -> str:
    """Keyword routing, used when the LLM router is unavailable or fails."""
    q = query.lower()
    if config == "bitemporal_pair":
        return "change"
    if config == "crossmodal_pair":
        return "fusion"
    if any(w in q for w in ["highlight", "locate", "point out", "where is", "mark "]):
        return "grounding"
    if any(w in q for w in ["describe", "caption", "scene", "overview"]):
        return "caption"
    return "vqa"


def llm_route(query: str, config: str) -> str | None:
    """Asks an LLM to pick a tool. Returns None if no key, no package, or a bad answer."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": (
                    f"Pick the single best tool for this remote sensing query.\n"
                    f"Tools:\n{describe_tools()}\n"
                    f"Input configuration: {config}\n"
                    f"Query: {query}\n"
                    f'Reply with JSON only: {{"tool": "<name>"}}'
                ),
            }],
        )
        choice = json.loads(msg.content[0].text.strip()).get("tool")
        if choice in TOOL_REGISTRY and config in TOOL_REGISTRY[choice].input_types:
            return choice
    except Exception:
        pass
    return None


def handle_query(query: str, validated_inputs: dict | None = None) -> dict:
    """Main entry point. Returns answer, spatial, confidence, trace."""
    inputs = validated_inputs or FAKE_VALIDATED_INPUTS
    config = normalize_input_config(inputs["config_type"])

    task = llm_route(query, config)
    routing_method = "llm_function_call" if task else "rule_based_fallback"
    if task is None:
        task = rule_route(query, config)

    tool = get_tool(task)
    if config not in tool.input_types:
        raise ValueError(f"task '{task}' does not accept input config '{config}'")

    results = [tool.run(inputs["images"], query)]

    trace = {
        "query": query,
        "task_selected": task,
        "input_config": config,
        "routing_method": routing_method,
        "tools_used": [
            {"name": r.metadata.get("model", task), "params": r.metadata.get("params", {})}
            for r in results
        ],
        "outputs": [
            {"text": r.text, "spatial": r.spatial, "confidence": r.confidence}
            for r in results
        ],
    }

    return {
        "answer": " ".join(r.text for r in results),
        "spatial": next((r.spatial for r in results if r.spatial), None),
        "confidence": aggregate_confidence(results),
        "trace": trace,
    }
