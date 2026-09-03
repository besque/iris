"""Streams a small BigEarthNet subset from HuggingFace and saves it as
PNGs + a labels jsonl. Run on the training machine, needs internet.

Usage: python scripts/prepare_bigearthnet.py [n_train] [n_val]
Output: data/bigearthnet_subset/{train,val}.jsonl + images/

If the default repo's schema differs, the script prints the actual columns,
then set IMAGE_KEY and LABEL_KEY below. Fallback dataset if HF streaming
fails: ben-ge-8k (https://github.com/HSG-AIML/ben-ge), 4.2GB archive.
"""

import json
import os
import sys

REPO = "BIFOLD-BigEarthNetv2-0/BigEarthNet.txt"
IMAGE_KEY = None   # auto-detect, or set by hand, e.g. "s2_rgb"
LABEL_KEY = None   # e.g. "labels"

N_TRAIN = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
N_VAL = int(sys.argv[2]) if len(sys.argv) > 2 else 800
OUT = "data/bigearthnet_subset"


def detect_keys(sample):
    from PIL import Image
    img_key, lbl_key = IMAGE_KEY, LABEL_KEY
    for k, v in sample.items():
        if img_key is None and isinstance(v, Image.Image):
            img_key = k
        if lbl_key is None and isinstance(v, list) and v and isinstance(v[0], (str, int)):
            lbl_key = k
    if not img_key or not lbl_key:
        print(f"could not auto-detect keys, columns are: {list(sample.keys())}")
        print("set IMAGE_KEY and LABEL_KEY at the top of this script")
        sys.exit(1)
    return img_key, lbl_key


def main():
    from datasets import load_dataset

    os.makedirs(f"{OUT}/images", exist_ok=True)
    ds = load_dataset(REPO, split="train", streaming=True)
    it = iter(ds)
    first = next(it)
    img_key, lbl_key = detect_keys(first)
    print(f"using image column '{img_key}', label column '{lbl_key}'")

    names = ds.features[lbl_key].feature.names if hasattr(ds.features.get(lbl_key, None), "feature") else None

    def label_text(raw):
        if names and raw and isinstance(raw[0], int):
            return [names[i] for i in raw]
        return [str(x) for x in raw]

    written = {"train": 0, "val": 0}
    files = {s: open(f"{OUT}/{s}.jsonl", "w") for s in written}
    for i, sample in enumerate([first] + list(next(it, None) for _ in range(N_TRAIN + N_VAL - 1))):
        if sample is None:
            break
        split = "train" if i < N_TRAIN else "val"
        img_path = f"{OUT}/images/{i:06d}.png"
        sample[img_key].convert("RGB").save(img_path)
        files[split].write(json.dumps({"image": img_path, "labels": label_text(sample[lbl_key])}) + "\n")
        written[split] += 1
        if i % 500 == 0:
            print(f"{i} done")
    for f in files.values():
        f.close()
    print(f"saved {written}")


if __name__ == "__main__":
    main()
