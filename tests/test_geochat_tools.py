"""Run: .venv/bin/python -m pytest tests/test_geochat_tools.py
No model needed: _call_geochat is stubbed with real GeoChat/Qwen output strings."""

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import geochat_backend as gc  # noqa: E402
from backend.tools.grounding.box_parser import parse_boxes, strip_boxes  # noqa: E402
from backend.tools.grounding.geochat_grounding import GeoChatGrounding, build_prompt  # noqa: E402
from backend.tools.vqa.geochat_vqa import GeoChatVQA  # noqa: E402

TMP = "/tmp/satquery_test"
os.makedirs(TMP, exist_ok=True)


def stub(reply):
    calls = []

    def fake(image, prompt):
        calls.append((image, prompt))
        return reply
    gc._call_geochat = fake
    return calls


def test_parse_geochat_box_normalised_0_100():
    text = "<p>water body</p> {<10><20><50><80>|<0>}"
    assert parse_boxes(text, 200, 100, scale=100) == [[20, 20, 100, 80]]


def test_parse_multiple_boxes_and_strip():
    text = "<p>building</p> {<0><0><10><10>|<45>} and <p>lake</p> {<50><50><100><100>|<0>}"
    assert parse_boxes(text, 100, 100, scale=100) == [[0, 0, 10, 10], [50, 50, 100, 100]]
    assert strip_boxes(text) == "building and lake"


def test_parse_qwen_box_0_1000():
    text = "The lake is here <|box_start|>(100,200),(300,400)<|box_end|>."
    assert parse_boxes(text, 500, 500, scale=1000) == [[50, 100, 150, 200]]
    assert "box_start" not in strip_boxes(text)


def test_parse_plain_pixels_and_clip():
    assert parse_boxes("box: [10, 20, 999, 40]", 100, 100, scale=0) == [[10, 20, 100, 40]]


def test_degenerate_or_missing_box_is_dropped():
    assert parse_boxes("{<5><5><5><9>|<0>}", 100, 100, 100) == []
    assert parse_boxes("There is no water body in this image.", 100, 100, 100) == []


def test_build_prompt_adds_refer_tag():
    assert build_prompt("highlight the water body") == "[refer] give me the location of the water body"
    assert build_prompt("Where is the lake?") == "[refer] give me the location of the lake"
    assert build_prompt("[grounding] describe the image") == "[grounding] describe the image"


def test_vqa_tool_result_shape():
    stub("Mostly farmland with a river.")
    path = os.path.join(TMP, "vqa.png")
    Image.new("RGB", (64, 48), (0, 120, 0)).save(path)
    r = GeoChatVQA().run([path], "What is shown?")
    assert r.text == "Mostly farmland with a river."
    assert r.confidence == 0.7
    assert r.metadata["confidence_source"] == "fixed"
    assert r.metadata["params"]["prompt"] == "What is shown?"
    assert r.spatial is None


def test_grounding_tool_pixels_from_numpy_input():
    calls = stub("<p>water body</p> {<25><50><75><100>|<0>}")
    arr = np.zeros((100, 200, 3), np.uint8)
    r = GeoChatGrounding().run(arr, "highlight the water body", coord_scale=100, presence_check=False)
    assert calls[0][1] == "[refer] give me the location of the water body"
    assert r.spatial == {"type": "bbox", "data": [[50, 50, 150, 100]]}
    assert r.confidence == 0.7
    assert r.metadata["raw_output"].startswith("<p>")


def test_grounding_tool_accepts_validator_dict_and_no_box():
    stub("There is no water body in this image.")
    path = os.path.join(TMP, "dry.png")
    Image.new("RGB", (32, 32)).save(path)
    r = GeoChatGrounding().run([{"path": path, "modality": "optical"}], "highlight the water body")
    assert r.spatial["data"] == []
    assert "No region found" in r.text
    assert r.confidence < 0.7


def test_grounding_retries_with_second_phrasing():
    replies = iter(["Yes", "The water body is at the bottom right.", "{<0><60><22><84>|<90>}"])
    calls = []

    def fake(image, prompt):
        calls.append(prompt)
        return next(replies)
    gc._call_geochat = fake
    r = GeoChatGrounding().run(np.zeros((512, 512, 3), np.uint8), "highlight the water body")
    assert len(calls) == 3 and calls[2].startswith("[refer] where is the water body?")
    assert r.spatial["data"] == [[0, 307, 113, 430]]
    assert r.metadata["params"]["prompts"] == calls[1:]
    assert r.metadata["presence_answer"] == "Yes"


def test_grounding_presence_check_blocks_hallucinated_box():
    calls = stub("No")
    r = GeoChatGrounding().run(np.zeros((64, 64, 3), np.uint8), "highlight the water body")
    assert len(calls) == 1 and calls[0][1] == "Is there the water body in this image? Answer yes or no."
    assert r.spatial["data"] == [] and r.text == "No water body found in the image."
    assert r.metadata["raw_output"] == "No"


def test_parse_real_geochat_output_with_delim():
    raw = ("In the satellite image, there are <p>some buildings</p> {<78><80><86><88>|<16>}<delim>"
           "{<67><78><75><86>|<16>} located close to each other.")
    assert parse_boxes(raw, 512, 512, 100) == [[399, 410, 440, 451], [343, 399, 384, 440]]
    assert "<delim>" not in strip_boxes(raw) and "some buildings" in strip_boxes(raw)


def test_load_image_handles_float_chw_array():
    arr = np.random.rand(3, 20, 30).astype(np.float32)
    im = gc.load_image(arr)
    assert im.size == (30, 20) and im.mode == "RGB"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
