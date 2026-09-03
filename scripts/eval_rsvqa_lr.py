"""Accuracy of GeoChatVQA on the RSVQA-LR test split (Lobry et al.).
Follows the GeoChat paper's protocol: presence, comparison and rural/urban
question types, "count" skipped, answers compared after normalising.
Writes evaluation/results/rsvqa_lr.md.

Data: https://zenodo.org/records/6344334 unpacked into data/rsvqa_lr/
  (LR_split_test_questions.json, LR_split_test_answers.json, Images_LR/*.tif)
Usage:
  GEOCHAT_ENDPOINT=http://localhost:5000 .venv/bin/python scripts/eval_rsvqa_lr.py --per-type 100"""

import argparse
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import geochat_backend as gc  # noqa: E402
from backend.tools.vqa.geochat_vqa import GeoChatVQA  # noqa: E402

DATA = "data/rsvqa_lr"
OUT = "evaluation/results/rsvqa_lr.md"
TYPES = ["presence", "comparison", "rural_urban"]
SUFFIX = " Answer the question using a single word or phrase."   # geochat's own eval prompt


def normalise(a: str) -> str:
    a = a.lower().strip()
    a = re.sub(r"[^a-z0-9 ]", " ", a)
    words = a.split()
    if not words:
        return ""
    if words[0] in ("yes", "no"):
        return words[0]
    for w in ("rural", "urban"):
        if w in words:
            return w
    return " ".join(words)


def load_split():
    qs = json.load(open(os.path.join(DATA, "LR_split_test_questions.json")))["questions"]
    ans = json.load(open(os.path.join(DATA, "LR_split_test_answers.json")))["answers"]
    gold = {a["question_id"]: a["answer"] for a in ans if a.get("active", True)}
    items = [q for q in qs if q.get("active", True) and q["type"] in TYPES and q["id"] in gold]
    return items, gold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-type", type=int, default=100, help="questions sampled per type")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    items, gold = load_split()
    rng = random.Random(args.seed)
    by_type = defaultdict(list)
    for q in items:
        by_type[q["type"]].append(q)
    sample = []
    for t in TYPES:
        rng.shuffle(by_type[t])
        sample += by_type[t][:args.per_type]
    print(f"{len(items)} eligible test questions, evaluating {len(sample)} "
          f"({args.per_type} per type) with {gc.model_name()} via {gc.backend_name()}\n")

    tool = GeoChatVQA()
    correct = defaultdict(int)
    seen = defaultdict(int)
    failures = []
    t0 = time.time()
    for i, q in enumerate(sample, 1):
        path = os.path.join(DATA, "Images_LR", f"{q['img_id']}.tif")
        pred_raw = tool.run([path], q["question"] + SUFFIX).text
        pred, truth = normalise(pred_raw), normalise(gold[q["id"]])
        ok = pred == truth
        seen[q["type"]] += 1
        correct[q["type"]] += ok
        if not ok and len(failures) < 30:
            failures.append((q["type"], q["question"], gold[q["id"]], pred_raw))
        if i % 25 == 0 or i == len(sample):
            acc = sum(correct.values()) / i
            print(f"  {i}/{len(sample)}  running accuracy {acc:.1%}  ({time.time() - t0:.0f}s)")

    overall = sum(correct.values()) / max(sum(seen.values()), 1)
    lines = [
        f"# RSVQA-LR test accuracy, {gc.model_name()} 4-bit ({date.today()})",
        "",
        f"{sum(seen.values())} questions sampled from the official test split (seed {args.seed}, "
        f"{args.per_type} per type), prompt suffix `{SUFFIX.strip()}`, zero-shot, no fine-tuning.",
        "Count questions skipped as in the GeoChat paper. Answers normalised (lowercase, first word for yes/no).",
        "",
        "| type | n | accuracy |",
        "|---|---|---|",
    ]
    for t in TYPES:
        if seen[t]:
            lines.append(f"| {t} | {seen[t]} | {correct[t] / seen[t]:.1%} |")
    lines.append(f"| **all** | {sum(seen.values())} | **{overall:.1%}** |")
    lines += ["", "For reference the GeoChat paper reports 91.1 / 90.3 / 94.0 (presence / comparison / rural-urban) on the full LR test set in fp16.",
              "", "## Sample of wrong answers", "", "| type | question | gold | model said |", "|---|---|---|---|"]
    for t, qu, g, p in failures:
        lines.append(f"| {t} | {qu} | {g} | {p} |")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(lines) + "\n")
    print(f"\noverall {overall:.1%}, wrote {OUT}")


if __name__ == "__main__":
    main()
