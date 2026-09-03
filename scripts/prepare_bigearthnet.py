"""Streams a BigEarthNet subset (GFM-Bench version: real S1+S2 pixels + labels)
and saves PNGs + a labels jsonl for CLIP fine-tuning.

Usage: python scripts/prepare_bigearthnet.py [n_train] [n_val]
Output: data/bigearthnet_subset/{train,val}.jsonl + images/

Optical rows say "a satellite image of ...", SAR rows "a SAR satellite image
of ...", so the model adapts to both modalities.
"""

import json
import os
import sys

import numpy as np

REPO = "GFM-Bench/BigEarthNet"
N_TRAIN = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
N_VAL = int(sys.argv[2]) if len(sys.argv) > 2 else 800
OUT = "data/bigearthnet_subset"
INCLUDE_SAR = True

# sentinel-2 12-band L2A order: B01,B02,B03,B04,... so RGB = B04,B03,B02
RGB_IDX = [3, 2, 1]


def to_chw(x) -> np.ndarray:
    """Accepts list/array/PIL, returns channels-first float array."""
    if hasattr(x, "convert"):
        x = np.asarray(x)
    a = np.asarray(x, dtype=np.float32)
    if a.ndim == 2:
        a = a[None]
    elif a.ndim == 3 and a.shape[0] > a.shape[2]:
        a = np.moveaxis(a, -1, 0)  # HWC -> CHW
    return a


def stretch_to_png(chw: np.ndarray, path: str):
    from PIL import Image
    out = np.zeros_like(chw)
    for i in range(chw.shape[0]):
        lo, hi = np.percentile(chw[i], 2), np.percentile(chw[i], 98)
        out[i] = np.clip((chw[i] - lo) / (hi - lo + 1e-6), 0, 1)
    arr = (np.moveaxis(out, 0, -1) * 255).astype(np.uint8)
    if arr.shape[2] == 1:
        arr = np.repeat(arr, 3, axis=2)
    Image.fromarray(arr).save(path)


def label_names(raw, feature):
    vals = raw if isinstance(raw, list) else [raw]
    names = []
    for v in vals:
        if isinstance(v, int):
            f = getattr(feature, "feature", feature)
            names.append(f.names[v] if hasattr(f, "names") else str(v))
        else:
            names.append(str(v))
    return names


def main():
    from datasets import get_dataset_split_names, load_dataset

    os.makedirs(f"{OUT}/images", exist_ok=True)
    splits = get_dataset_split_names(REPO)
    split = "train" if "train" in splits else splits[0]
    print(f"using split '{split}' (available: {splits})")
    ds = load_dataset(REPO, split=split, streaming=True)

    files = {s: open(f"{OUT}/{s}.jsonl", "w") for s in ("train", "val")}
    n = 0
    for sample in ds:
        if n == 0:
            print("columns:", list(sample.keys()))
            if "optical" not in sample or "label" not in sample:
                print("expected 'optical' and 'label' columns, adjust the script")
                sys.exit(1)
        if n >= N_TRAIN + N_VAL:
            break
        split_name = "train" if n < N_TRAIN else "val"
        labels = label_names(sample["label"], ds.features["label"])

        opt = to_chw(sample["optical"])
        rgb = opt[RGB_IDX] if opt.shape[0] >= 4 else opt[:3]
        opt_path = f"{OUT}/images/{n:06d}_opt.png"
        stretch_to_png(rgb, opt_path)
        files[split_name].write(json.dumps(
            {"image": opt_path, "labels": labels, "modality": "optical"}) + "\n")

        if INCLUDE_SAR and "radar" in sample:
            sar = to_chw(sample["radar"])[:1]
            sar_path = f"{OUT}/images/{n:06d}_sar.png"
            stretch_to_png(sar, sar_path)
            files[split_name].write(json.dumps(
                {"image": sar_path, "labels": labels, "modality": "sar"}) + "\n")

        n += 1
        if n % 250 == 0:
            print(f"{n} samples done")

    for f in files.values():
        f.close()
    print(f"saved {n} samples ({N_TRAIN} train / {n - N_TRAIN} val) to {OUT}")


if __name__ == "__main__":
    main()
