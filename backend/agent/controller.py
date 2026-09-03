"""Agent controller — the brain of SatQuery.

Responsibilities (from the problem statement):
1. Interpret the user's query and classify the task
   (vqa / caption / grounding / change / fusion).
2. Check the validated input configuration matches the task
   (e.g. change detection needs exactly 2 images of the same area).
3. Select tool(s) from the registry and plan the execution order.
4. Execute tools with permitted parameters only.
5. Hand results to reporting for combination + evidence.
6. Record an auditable execution trace: task, tools, params, outputs.
"""


def handle_query(query: str, validated_inputs: dict) -> dict:
    """Main entry point called by the API layer.

    Returns: {answer, spatial_evidence, confidence, execution_trace}
    """
    raise NotImplementedError
