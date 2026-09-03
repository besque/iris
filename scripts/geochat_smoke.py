"""Smoke test for the GPU box (no notebook needed). Loads the model through
backend/tools/geochat_backend.py, asks one VQA question, runs the grounding
prompts and prints the RAW box text so we can confirm the format.

Usage on the GPU machine, with the GeoChat repo on PYTHONPATH:
  GEOCHAT_BACKEND=local python scripts/geochat_smoke.py [image.png]
  GEOCHAT_BACKEND=qwen  python scripts/geochat_smoke.py [image.png]   (fallback)
Writes smoke_boxes.png next to the image with the parsed boxes drawn on."""

import io
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import geochat_backend as gc  # noqa: E402
from backend.tools.grounding.box_parser import parse_boxes  # noqa: E402
from backend.tools.grounding.geochat_grounding import GeoChatGrounding  # noqa: E402
from backend.tools.vqa.geochat_vqa import GeoChatVQA  # noqa: E402

# lake + shoreline so "where is the water body" has an obvious answer
DEFAULT_URL = "https://upload.wikimedia.org/wikipedia/commons/4/4c/Lake_Tahoe_from_space%2C_Landsat_8.jpg"
MAX_SIDE = 1024   # wikimedia thumbnails 400 on odd sizes, so fetch the original and shrink here
GROUNDING_PROMPTS = [
    "[refer] give me the location of the water body",
    "[refer] give me the location of the lake",
    "[grounding] describe the image",
]


def synthetic_lake():
    """Green land, a dark blue lake top-left, a grey town bottom-right. Good
    enough to prove loading and the box format when no real image is handy."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(0)
    arr = (rng.normal(0, 8, (512, 512, 3)) + (80, 120, 60)).clip(0, 255).astype(np.uint8)
    arr[60:220, 40:260] = (30, 60, 140)
    arr[330:470, 300:480] = (165, 160, 150)
    return Image.fromarray(arr)


def get_image(arg):
    from PIL import Image
    if arg:
        return Image.open(arg).convert("RGB"), arg
    path = "smoke_input.png"
    try:
        import requests
        r = requests.get(DEFAULT_URL, timeout=60,
                         headers={"User-Agent": "satquery-smoke-test (student project)"})
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE))
    except Exception as e:
        print(f"download failed ({type(e).__name__}), using a synthetic lake scene instead. "
              f"pass a real image path as argv[1] for a meaningful VQA answer")
        im = synthetic_lake()
    im.save(path)
    return im, path


def main():
    import torch
    print(f"torch {torch.__version__}, cuda available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print("gpu:", torch.cuda.get_device_name(0))
    print(f"backend: {gc.backend_name()}   model: {gc.model_name()}   box scale: 0-{gc.coord_scale()}\n")

    image, path = get_image(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"image: {path}  size (w, h): {image.size}\n")

    t = time.time()
    raw = gc._call_geochat(image, "What is shown in this image?")
    print(f"[load + first call took {time.time() - t:.0f}s]")
    print("VQA  Q: What is shown in this image?")
    print("VQA  A:", raw, "\n")
    assert raw.strip(), "empty VQA answer"

    all_nums = []
    for prompt in GROUNDING_PROMPTS:
        t = time.time()
        raw = gc._call_geochat(image, prompt)
        print(f"PROMPT: {prompt}   ({time.time() - t:.1f}s)")
        print(f"RAW   : {raw!r}")
        boxes = parse_boxes(raw, *image.size, gc.coord_scale())
        print(f"PARSED: {boxes if boxes else 'no box parsed'}\n")
        all_nums += [float(n) for n in re.findall(r"<\s*(-?\d+(?:\.\d+)?)\s*>", raw)]

    if all_nums:
        print(f"{len(all_nums)} numbers in <n> tags, min {min(all_nums)}, max {max(all_nums)}")
        if max(all_nums) <= 100:
            print("=> consistent with 0-100 normalised coords, parser scale is right")
        else:
            print("=> NOT 0-100. set GEOCHAT_COORD_SCALE or fix COORD_SCALES in geochat_backend.py")
    else:
        print("no <n> tags in any output: box format differs from the paper, "
              "paste the RAW lines above into tests/test_geochat_tools.py and adjust box_parser.py")

    print("\n--- through the Tool classes, as the controller calls them ---")
    r = GeoChatVQA().run([path], "What land cover types are visible?")
    print("vqa      :", r.text, "| conf", r.confidence)
    r = GeoChatGrounding().run([path], "highlight the water body")
    print("grounding:", r.text, "| boxes", r.spatial["data"], "| conf", r.confidence)

    if r.spatial["data"]:
        from PIL import ImageDraw
        out = image.copy()
        d = ImageDraw.Draw(out)
        for b in r.spatial["data"]:
            d.rectangle(b, outline="red", width=4)
        out_path = os.path.join(os.path.dirname(os.path.abspath(path)), "smoke_boxes.png")
        out.save(out_path)
        print(f"\nboxes drawn to {out_path} (scp it back and look: is the box on the water?)")
        print("SMOKE TEST PASSED")
    else:
        print("\nno box for the water body. model loaded and answered, but grounding needs a look")
        sys.exit(2)


if __name__ == "__main__":
    main()
