"""Scores GeoChat on BigEarthNet.txt yes/no and multiple-choice questions.
Needs data/bigearthnet_txt/qa_sample.json + images (made on the GPU box, rsynced here)
and a running GeoChat endpoint.
Usage: GEOCHAT_ENDPOINT=http://localhost:5000 .venv/bin/python scripts/eval_bigearthnet_txt_qa.py"""

import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import geochat_backend as gc  # noqa: E402

SAMPLE = "data/bigearthnet_txt/qa_sample.json"
OUT = "evaluation/results/bigearthnet_txt_qa.md"


def normalise(kind, text):
    t = text.strip().lower()
    if kind == "binary":
        return "yes" if t.startswith("yes") else "no" if t.startswith("no") else t.split()[0] if t else ""
    m = re.match(r"\(?([a-d])\)?[\s.:)]", t + " ")
    return m.group(1) if m else t[:1]


def main():
    rows = json.load(open(SAMPLE))
    per_type, per_cat, wrong = collections.Counter(), collections.Counter(), []
    n_type, n_cat = collections.Counter(), collections.Counter()
    for i, r in enumerate(rows):
        img = gc.load_image(r["image"])
        suffix = " Answer yes or no." if r["type"] == "binary" else " Answer with the option letter only."
        pred = normalise(r["type"], gc._call_geochat(img, r["question"] + suffix))
        gold = normalise(r["type"], r["answer"])
        ok = pred == gold
        per_type[r["type"]] += ok
        per_cat[r["category"]] += ok
        n_type[r["type"]] += 1
        n_cat[r["category"]] += 1
        if not ok and len(wrong) < 15:
            wrong.append((r["type"], r["question"][:90], gold, pred))
        if i % 50 == 0:
            print(f"{i}/{len(rows)}")

    lines = [f"# GeoChat-7B 4-bit zero-shot on BigEarthNet.txt QA ({len(rows)} sampled questions)\n",
             "| type | n | accuracy |", "|---|---|---|"]
    for t in n_type:
        lines.append(f"| {t} | {n_type[t]} | {100 * per_type[t] / n_type[t]:.1f}% |")
    lines.append(f"| **all** | {len(rows)} | **{100 * sum(per_type.values()) / len(rows):.1f}%** |")
    lines += ["", "| category | n | accuracy |", "|---|---|---|"]
    for c in sorted(n_cat):
        lines.append(f"| {c} | {n_cat[c]} | {100 * per_cat[c] / n_cat[c]:.1f}% |")
    lines += ["", "## Sample of wrong answers", "", "| type | question | gold | model |", "|---|---|---|---|"]
    lines += [f"| {t} | {q} | {g} | {p} |" for t, q, g, p in wrong]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
