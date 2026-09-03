"""Downloads ben-ge-8k (BigEarthNet patches: Sentinel-1 + Sentinel-2 GeoTIFFs
plus land-cover labels, 1.8GB) and saves PNGs + a labels jsonl for training.

Usage: python scripts/prepare_bigearthnet.py [n_train] [n_val]
Output: data/bigearthnet_subset/{train,val}.jsonl + images/
Needs: pip install rasterio numpy
"""

import csv
import glob
import json
import os
import subprocess
import sys

import numpy as np

URL = "https://zenodo.org/records/8121208/files/ben-ge-8k.tar.gz?download=1"
RAW = "data/ben-ge-8k"
OUT = "data/bigearthnet_subset"
N_TRAIN = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
N_VAL = int(sys.argv[2]) if len(sys.argv) > 2 else 800
FRACTION_MIN = 0.10   # a class counts as a label if it covers >10% of the patch


def download_and_extract():
    os.makedirs(RAW, exist_ok=True)
    tar = os.path.join(RAW, "ben-ge-8k.tar.gz")
    if not glob.glob(f"{RAW}/**/sentinel-2", recursive=True):
        if not os.path.exists(tar):
            print("downloading 1.8GB from zenodo...")
            subprocess.run(["curl", "-L", "-C", "-", "-o", tar, URL], check=True)
        print("extracting...")
        subprocess.run(["tar", "xzf", tar, "-C", RAW], check=True)


def find_one(pattern):
    hits = glob.glob(pattern, recursive=True)
    return hits[0] if hits else None


def read_rgb_png(band_paths_or_file, out_path, bands=None):
    import rasterio
    from PIL import Image
    if isinstance(band_paths_or_file, list):
        chans = []
        for p in band_paths_or_file:
            with rasterio.open(p) as src:
                chans.append(src.read(1).astype(np.float32))
        arr = np.stack(chans)
    else:
        with rasterio.open(band_paths_or_file) as src:
            data = src.read().astype(np.float32)
        arr = data[bands] if bands else data[:3]
    out = np.zeros_like(arr)
    for i in range(arr.shape[0]):
        lo, hi = np.percentile(arr[i], 2), np.percentile(arr[i], 98)
        out[i] = np.clip((arr[i] - lo) / (hi - lo + 1e-6), 0, 1)
    img = (np.moveaxis(out, 0, -1) * 255).astype(np.uint8)
    if img.shape[2] == 1:
        img = np.repeat(img, 3, axis=2)
    Image.fromarray(img).save(out_path)


def main():
    download_and_extract()
    os.makedirs(f"{OUT}/images", exist_ok=True)

    lc_csv = find_one(f"{RAW}/**/*esaworldcover*.csv")
    if not lc_csv:
        print(f"no esaworldcover csv found under {RAW}, contents:")
        subprocess.run(["find", RAW, "-maxdepth", "3", "-type", "d"])
        sys.exit(1)

    with open(lc_csv) as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    print(f"label csv columns: {cols}")
    id_col = next(c for c in cols if "patch" in c.lower() and "s1" not in c.lower())
    s1_col = next((c for c in cols if "s1" in c.lower()), None)
    frac_cols = [c for c in cols if c not in (id_col, s1_col)
                 and rows[0][c].replace(".", "", 1).replace("-", "", 1).isdigit()]
    print(f"using id column '{id_col}', {len(frac_cols)} class columns")

    files = {s: open(f"{OUT}/{s}.jsonl", "w") for s in ("train", "val")}
    n = 0
    for row in rows:
        if n >= N_TRAIN + N_VAL:
            break
        pid = row[id_col]
        labels = [c.replace("_", " ").strip() for c in frac_cols
                  if float(row[c] or 0) > FRACTION_MIN]
        if not labels:
            continue
        split = "train" if n < N_TRAIN else "val"

        s2_dir = find_one(f"{RAW}/**/sentinel-2/**/{pid}*")
        if not s2_dir:
            continue
        b = {name: find_one(f"{s2_dir}/**/*_{name}.tif*") or find_one(f"{s2_dir}/*_{name}.tif*")
             for name in ("B04", "B03", "B02")}
        opt_png = f"{OUT}/images/{n:06d}_opt.png"
        if all(b.values()):
            read_rgb_png([b["B04"], b["B03"], b["B02"]], opt_png)
        else:
            single = find_one(f"{s2_dir}/*.tif*")
            if not single:
                continue
            read_rgb_png(single, opt_png, bands=[3, 2, 1])
        files[split].write(json.dumps(
            {"image": opt_png, "labels": labels, "modality": "optical"}) + "\n")

        s1_id = row.get(s1_col, pid) if s1_col else pid
        s1_dir = find_one(f"{RAW}/**/sentinel-1/**/{s1_id}*")
        vv = find_one(f"{s1_dir}/**/*VV*.tif*") or find_one(f"{s1_dir}/*VV*.tif*") if s1_dir else None
        if vv:
            sar_png = f"{OUT}/images/{n:06d}_sar.png"
            read_rgb_png([vv], sar_png)
            files[split].write(json.dumps(
                {"image": sar_png, "labels": labels, "modality": "sar"}) + "\n")

        n += 1
        if n % 250 == 0:
            print(f"{n} patches done")

    for f in files.values():
        f.close()
    print(f"saved {n} patches to {OUT}")
    if n == 0:
        print("nothing matched, inspect the layout:")
        subprocess.run(["find", RAW, "-maxdepth", "4", "-type", "d"])


if __name__ == "__main__":
    main()
