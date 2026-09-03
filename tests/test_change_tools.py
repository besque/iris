import pytest

from backend.tools.change import ChangeTool
from backend.tools.base import ToolResult


class FakeChangeModel:
    def predict(self, image_t1, image_t2, question):
        return "A building area increased between T1 and T2."


def test_change_tool_returns_tool_result():
    tool = ChangeTool(model=FakeChangeModel())

    result = tool.run(
        images=["image_t1", "image_t2"],
        query="What changed between the two images?",
    )

    assert isinstance(result, ToolResult)
    assert result.text == "A building area increased between T1 and T2."
    assert result.metadata["tool"] == "change"
    assert result.metadata["input_type"] == "bitemporal_pair"


def test_change_tool_requires_two_images():
    tool = ChangeTool(model=FakeChangeModel())

    with pytest.raises(ValueError):
        tool.run(
            images=["only_one_image"],
            query="What changed?",
        )


def test_change_tool_requires_question():
    tool = ChangeTool(model=FakeChangeModel())

    with pytest.raises(ValueError):
        tool.run(
            images=["image_t1", "image_t2"],
            query="",
        )