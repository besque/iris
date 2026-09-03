"""Runs the fusion tool on real Sentinel-1/Sentinel-2 pairs from ben-ge-8k
and saves side-by-side PNGs to eyeball. Run on the machine that has the data.

Usage: python scripts/check_fusion_real.py [n_pairs]
Output: data/fusion_check/<patch>_{rgb,sar,overlay}.png
"""

import csv
import glob
import os
import sys

import numpy as np
import rasterio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocessing.validator import to_rgb, validate_inputs  # noqa: E402
from backend.tools.fusion.fusion_tool import FusionTool  # noqa: E402

RAW = "data/ben-ge-8k"
OUT = "data/fusion_check"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5


def find_one(pattern):
    hits = sorted(glob.glob(pattern, recursive=True))
    return hits[0] if hits else None


def stack_s2(s2_dir, out_path):
    """Per-band tifs to one 4-band file in B,G,R,NIR order."""
    bands = []
    for name in ("B02", "B03", "B04", "B08"):
        p = find_one(f"{s2_dir}/**/*{name}.tif*") or find_one(f"{s2_dir}/*{name}.tif*")
        if not p:
            return None
        with rasterio.open(p) as src:
            bands.append(src.read(1))
            profile = src.profile
    profile.update(count=4)
    with rasterio.open(out_path, "w", **profile) as dst:
        for i, b in enumerate(bands, 1):
            dst.write(b, i)
    return out_path


def overlay(rgb, mask, out_path):
    from PIL import Image
    img = rgb.copy()
    img[mask == 1] = (0.4 * img[mask == 1] + 0.6 * np.array([0, 90, 255])).astype(np.uint8)
    img[mask == 2] = (0.4 * img[mask == 2] + 0.6 * np.array([255, 140, 0])).astype(np.uint8)
    Image.fromarray(img).save(out_path)


def main():
    os.makedirs(OUT, exist_ok=True)
    meta_csv = find_one(f"{RAW}/**/*meta*.csv")
    if not meta_csv:
        print(f"no meta csv under {RAW}")
        sys.exit(1)
    with open(meta_csv) as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    print(f"meta columns: {cols}")
    id_col = next(c for c in cols if "patch" in c.lower() and "s1" not in c.lower())
    s1_col = next((c for c in cols if "s1" in c.lower()), None)

    done = 0
    tool = FusionTool()
    for row in rows:
        if done >= N:
            break
        pid = row[id_col]
        s2_dir = find_one(f"{RAW}/**/sentinel-2/**/{pid}*")
        s1_id = row.get(s1_col, pid) if s1_col else pid
        s1_dir = find_one(f"{RAW}/**/sentinel-1/**/{s1_id}*")
        vv = (find_one(f"{s1_dir}/**/*VV*.tif*") or find_one(f"{s1_dir}/*VV*.tif*")) if s1_dir else None
        if not s2_dir or not vv:
            continue
        opt_path = stack_s2(s2_dir, f"{OUT}/{done}_s2_stack.tif")
        if not opt_path:
            continue

        val = validate_inputs([opt_path, vv])
        print(f"\npair {done} ({pid}): {val['config_type']}")
        res = tool.run(val["images"], "identify built-up and water regions")
        print(" ", res.text)
        print("  confidence:", res.confidence)

        rgb = to_rgb(opt_path)
        from PIL import Image
        Image.fromarray(rgb).save(f"{OUT}/{done}_rgb.png")
        Image.fromarray(to_rgb(vv)).save(f"{OUT}/{done}_sar.png")
        mask = res.spatial["data"]
        if mask.shape != rgb.shape[:2]:
            mask = np.asarray(Image.fromarray(mask).resize((rgb.shape[1], rgb.shape[0]), Image.NEAREST))
        overlay(rgb, mask, f"{OUT}/{done}_overlay.png")
        done += 1

    print(f"\nsaved {done} pairs to {OUT}/ (blue = water, orange = built-up)")
    if done == 0:
        print("no pairs matched, layout:")
        os.system(f"find {RAW} -maxdepth 4 -type d | head -20")


if __name__ == "__main__":
    main()
