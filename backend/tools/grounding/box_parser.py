"""Turns a VLM's box text into pixel [x1, y1, x2, y2] lists.

GeoChat writes boxes as {<x1><y1><x2><y2>|<angle>} with each coordinate in
0-100 of the image side (the paper's format, angle is the rotation in degrees,
we drop it). Qwen2-VL writes <|box_start|>(x1,y1),(x2,y2)<|box_end|> in 0-1000.
Plain [x1, y1, x2, y2] or (x1, y1, x2, y2) also parses so a hand-written
fallback still works. The caller tells us the scale, we do not guess."""

import re

_TAGGED = re.compile(r"\{?\s*<\s*(-?\d+(?:\.\d+)?)\s*>\s*<\s*(-?\d+(?:\.\d+)?)\s*>\s*<\s*(-?\d+(?:\.\d+)?)\s*>\s*<\s*(-?\d+(?:\.\d+)?)\s*>")
_QWEN = re.compile(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)\s*,\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
_PLAIN = re.compile(r"[\[(]\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*[\])]")
_PHRASE = re.compile(r"<p>(.*?)</p>")


def find_raw_boxes(text: str) -> list[list[float]]:
    """Every box in the text, in the model's own units, in order of appearance."""
    hits = []
    for pat in (_TAGGED, _QWEN, _PLAIN):
        for m in pat.finditer(text):
            hits.append((m.start(), [float(v) for v in m.groups()]))
    hits.sort(key=lambda h: h[0])
    return [box for _, box in hits]


def to_pixels(box: list[float], width: int, height: int, scale: float) -> list[int]:
    """scale is the model's coordinate range per side (100 for GeoChat, 1000
    for Qwen2-VL, 1 for 0-1 floats, 0 or None means already pixels)."""
    x1, y1, x2, y2 = box
    if scale:
        x1, x2 = x1 / scale * width, x2 / scale * width
        y1, y2 = y1 / scale * height, y2 / scale * height
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    return [
        int(round(min(max(x1, 0), width))), int(round(min(max(y1, 0), height))),
        int(round(min(max(x2, 0), width))), int(round(min(max(y2, 0), height))),
    ]


def parse_boxes(text: str, width: int, height: int, scale: float) -> list[list[int]]:
    out = []
    for raw in find_raw_boxes(text):
        px = to_pixels(raw, width, height, scale)
        if px[2] > px[0] and px[3] > px[1]:
            out.append(px)
    return out


def strip_boxes(text: str) -> str:
    """Human-readable version of the answer: box tokens gone, phrases kept."""
    text = re.sub(r"\{\s*<[^}]*>\s*\}", "", text)
    text = re.sub(r"(<\s*-?\d+(?:\.\d+)?\s*>){4}(\|<[^>]*>)?", "", text)
    text = re.sub(r"<\|box_start\|>.*?<\|box_end\|>", "", text)
    text = re.sub(r"<\|object_ref_start\|>|<\|object_ref_end\|>|<delim>", "", text)
    text = _PHRASE.sub(r"\1", text)
    return re.sub(r"\s{2,}", " ", text).strip(" ,.;") or text.strip()
