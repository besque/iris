"""Joins the BigEarthNet.txt annotations (HF: BIFOLD-BigEarthNetv2-0/BigEarthNet.txt)
onto the ben-ge-8k patches we already have, by patch id. v2 ids are the v1 ids
with a tile segment inserted: S2A_..._20170613T101031_N9999_R022_T33UUP_26_57.

Run on the GPU box after prepare_bigearthnet.py:
    python scripts/prepare_bigearthnet_txt.py
Output: data/bigearthnet_txt/{train,val}.jsonl (captions, for CLIP) and qa.jsonl (for VQA eval)
"""

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.prepare_bigearthnet import find_one, read_rgb_png  # noqa: E402

REPO = "BIFOLD-BigEarthNetv2-0/BigEarthNet.txt"
RAW = "data/ben-ge-8k"
OUT = "data/bigearthnet_txt"
VAL_FRACTION = 0.15
TILE_SEG = re.compile(r"_N\d{4}_R\d{3}_T\w{5}")


def main():
    from datasets import load_dataset

    os.makedirs(f"{OUT}/images", exist_ok=True)
    s2_dirs = {os.path.basename(p.rstrip("/")): p
               for p in glob.glob(f"{RAW}/**/sentinel-2/*/", recursive=True)}
    print(f"{len(s2_dirs)} ben-ge patches on disk")

    ds = load_dataset(REPO, split="all_data", streaming=True)
    captions, qa = {}, []
    seen = 0
    for row in ds:
        seen += 1
        v1 = TILE_SEG.sub("", row["patch_id"])
        if v1 not in s2_dirs:
            continue
        if row["type"] == "captioning":
            captions.setdefault(v1, []).append(row["output"])
        else:
            qa.append({"patch_id": v1, "question": row["input"], "answer": row["output"],
                       "type": row["type"], "category": row["category"]})
        if seen % 200000 == 0:
            print(f"{seen} rows scanned, {len(captions)} patches with captions, {len(qa)} qa")

    print(f"done: {seen} rows, {len(captions)} matched patches with captions, {len(qa)} qa pairs")
    if not captions:
        print("no matches, check the id mapping (print a few row['patch_id'] values)")
        sys.exit(1)

    with open(f"{OUT}/qa.jsonl", "w") as f:
        for q in qa:
            png = f"{OUT}/images/{q['patch_id']}.png"
            q["image"] = png
            f.write(json.dumps(q) + "\n")

    files = {"train": open(f"{OUT}/train.jsonl", "w"), "val": open(f"{OUT}/val.jsonl", "w")}
    ids = sorted(captions)
    n_val = int(len(ids) * VAL_FRACTION)
    for i, pid in enumerate(ids):
        png = f"{OUT}/images/{pid}.png"
        if not os.path.exists(png):
            s2 = s2_dirs[pid]
            b = {n: find_one(f"{s2}/**/*_{n}.tif*") or find_one(f"{s2}/*_{n}.tif*") for n in ("B04", "B03", "B02")}
            if not all(b.values()):
                continue
            read_rgb_png([b["B04"], b["B03"], b["B02"]], png)
        split = "val" if i < n_val else "train"
        for cap in captions[pid]:
            files[split].write(json.dumps({"image": png, "text": cap, "labels": [], "modality": "optical"}) + "\n")
        if i % 500 == 0:
            print(f"{i} patches written")
    for f in files.values():
        f.close()
    print(f"saved to {OUT}")


if __name__ == "__main__":
    main()
