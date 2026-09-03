from backend.tools.base import Tool, ToolResult

from .model import ChangeModel


class ChangeTool(Tool):
    """
    Tool for analyzing changes between two bi-temporal
    remote-sensing images.
    """

    name = "change"

    description = (
        "Analyzes two remote-sensing images acquired at "
        "different times and answers questions about changes."
    )

    input_types = ["bitemporal_pair"]

    def __init__(self, model: ChangeModel | None = None):
        self.model = model or ChangeModel()

    def run(
        self,
        images: list,
        query: str,
        **params,
    ) -> ToolResult:
        """
        Analyze a bi-temporal image pair.

        images:
            [image_t1, image_t2]

        query:
            Natural-language question about the change.
        """

        if len(images) != 2:
            raise ValueError(
                "ChangeTool requires exactly two images: "
                "[image_t1, image_t2]."
            )

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        answer = self.model.predict(
            image_t1=images[0],
            image_t2=images[1],
            question=query,
        )

        return ToolResult(
            text=answer,
            metadata={
                "tool": self.name,
                "input_type": "bitemporal_pair",
            },
        )