"""Tries several grounding phrasings per object and records which ones make
GeoChat return a box. Writes evaluation/results/grounding_phrasings.md.

Usage (model served from the GPU box, see scripts/serve_geochat.py):
  GEOCHAT_ENDPOINT=http://localhost:5000 .venv/bin/python scripts/grounding_phrasings.py"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import geochat_backend as gc  # noqa: E402
from backend.tools.grounding.box_parser import parse_boxes  # noqa: E402

OUT = "evaluation/results/grounding_phrasings.md"

# image -> objects that are actually in it
CASES = {
    "data/samples/waterview.jpg": ["the water body", "the lake", "the bridge"],
    "data/samples/11760.jpg": ["the buildings", "the road"],
    "data/samples/11765.jpg": ["the buildings", "the road"],
}

PHRASINGS = [
    "[refer] give me the location of {obj}",
    "[refer] where is {obj}?",
    "[refer] where is {obj}? give me its bounding box",
    "[refer] {obj}",
    "[refer] locate {obj} in the image",
    "[grounding] highlight {obj}",
]


def main():
    image_paths = [p for p in CASES if os.path.exists(p)]
    if not image_paths:
        sys.exit("no sample images found, put some in data/samples/ first")
    scale = gc.coord_scale()
    rows, hits = [], {p: 0 for p in PHRASINGS}
    total = {p: 0 for p in PHRASINGS}

    for path in image_paths:
        image = gc.load_image(path)
        for obj in CASES[path]:
            for tmpl in PHRASINGS:
                prompt = tmpl.format(obj=obj)
                raw = gc._call_geochat(image, prompt)
                boxes = parse_boxes(raw, *image.size, scale)
                total[tmpl] += 1
                hits[tmpl] += bool(boxes)
                rows.append((os.path.basename(path), obj, tmpl, raw, len(boxes)))
                print(f"{os.path.basename(path):14} {obj:16} {tmpl:52} -> {'BOX' if boxes else 'no box':6} {raw!r}")

    lines = [
        f"# Grounding phrasings, GeoChat-7B 4-bit ({date.today()})",
        "",
        f"Model: {gc.model_name()} via {gc.backend_name()} backend. Boxes parsed by",
        "backend/tools/grounding/box_parser.py, coordinate scale 0-100.",
        "",
        "## Box hit rate per phrasing",
        "",
        "| phrasing | boxes returned | of prompts |",
        "|---|---|---|",
    ]
    for tmpl in sorted(PHRASINGS, key=lambda t: -hits[t] / max(total[t], 1)):
        lines.append(f"| `{tmpl}` | {hits[tmpl]} | {total[tmpl]} |")
    lines += ["", "## Every prompt and raw answer", "", "| image | object | phrasing | boxes | raw output |", "|---|---|---|---|---|"]
    for img, obj, tmpl, raw, n in rows:
        lines.append(f"| {img} | {obj} | `{tmpl}` | {n} | `{raw.replace('|', '\\|')}` |")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(lines) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
