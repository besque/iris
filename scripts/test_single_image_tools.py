"""Runs GeoChatVQA and GeoChatGrounding on 3 sample images and prints what
came back. Person 1 runs this before swapping the mocks in the registry.

Point the tool at a model first (see backend/tools/geochat_backend.py):
  GEOCHAT_ENDPOINT=https://xxxx.trycloudflare.com  (Colab notebook serve cell)
  or GEOCHAT_BACKEND=local / qwen on a GPU machine
Usage: .venv/bin/python scripts/test_single_image_tools.py"""

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import geochat_backend as gc  # noqa: E402
from backend.tools.grounding.geochat_grounding import GeoChatGrounding  # noqa: E402
from backend.tools.vqa.geochat_vqa import GeoChatVQA  # noqa: E402

SAMPLE_DIR = os.environ.get("SAMPLE_DIR", "data/samples")
VQA_QUESTION = "What land cover types are visible?"
GROUNDING_QUERY = "highlight the water body"
MAX_IMAGES = 3


def find_images(folder):
    exts = ("*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff")
    paths = sorted(p for e in exts for p in glob.glob(os.path.join(folder, e)))
    return paths[:MAX_IMAGES]


def make_synthetic(folder):
    """Three toy scenes so the pipeline can be smoke-tested with no downloads."""
    import numpy as np
    from PIL import Image

    os.makedirs(folder, exist_ok=True)
    rng = np.random.default_rng(0)
    scenes = {
        "synthetic_lake.png": lambda a: a.__setitem__((slice(20, 90), slice(30, 120)), (40, 80, 160)),
        "synthetic_town.png": lambda a: a.__setitem__((slice(100, 200), slice(120, 220)), (170, 160, 150)),
        "synthetic_fields.png": lambda a: None,
    }
    out = []
    for name, paint in scenes.items():
        arr = (rng.normal(0, 8, (256, 256, 3)) + (70, 110, 50)).clip(0, 255).astype(np.uint8)
        paint(arr)
        path = os.path.join(folder, name)
        Image.fromarray(arr).save(path)
        out.append(path)
    print(f"no images in {folder}, wrote 3 synthetic scenes there instead\n")
    return out


def fmt_boxes(boxes):
    if not boxes:
        return "no region found"
    return "; ".join(f"[x1={b[0]}, y1={b[1]}, x2={b[2]}, y2={b[3]}]" for b in boxes)


def main():
    backend = gc.backend_name()
    if backend == "http" and not os.environ.get("GEOCHAT_ENDPOINT"):
        sys.exit("set GEOCHAT_ENDPOINT to the tunnel URL from the notebook (or GEOCHAT_BACKEND=local/qwen)")
    print(f"backend: {backend}   model: {gc.model_name()}   box scale: 0-{gc.coord_scale()}\n")

    images = find_images(SAMPLE_DIR) or make_synthetic(SAMPLE_DIR)
    vqa, grounding = GeoChatVQA(), GeoChatGrounding()
    failures = 0

    for i, path in enumerate(images, 1):
        print("=" * 72)
        print(f"[{i}/{len(images)}] {path}")
        print("-" * 72)

        try:
            r = vqa.run([path], VQA_QUESTION)
            print(f"  Q: {VQA_QUESTION}")
            print(f"  A: {r.text}")
            print(f"  confidence: {r.confidence} ({r.metadata['confidence_source']})")
        except Exception as e:  # keep going, the next image may still work
            failures += 1
            print(f"  VQA FAILED: {type(e).__name__}: {e}")

        print()
        try:
            r = grounding.run([path], GROUNDING_QUERY)
            boxes = (r.spatial or {}).get("data") or []
            print(f"  Q: {GROUNDING_QUERY}")
            print(f"  A: {r.text}")
            print(f"  boxes (pixels, image {r.metadata['image_size'][0]}x{r.metadata['image_size'][1]}): {fmt_boxes(boxes)}")
            print(f"  confidence: {r.confidence} ({r.metadata['confidence_source']})")
            print(f"  raw model output: {r.metadata['raw_output']!r}")
        except Exception as e:
            failures += 1
            print(f"  GROUNDING FAILED: {type(e).__name__}: {e}")
        print()

    print("=" * 72)
    print("all calls succeeded" if not failures else f"{failures} call(s) failed, see above")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
