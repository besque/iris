"""Scores GeoChat on a VRSBench sample: VQA accuracy per question type and
captioning BLEU. Needs data/vrsbench/sample.json + images_sample/ and a GeoChat endpoint.
Usage: GEOCHAT_ENDPOINT=http://localhost:5000 .venv/bin/python scripts/eval_vrsbench.py"""

import collections
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import geochat_backend as gc  # noqa: E402

ROOT = "data/vrsbench"
OUT = "evaluation/results/vrsbench.md"


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return " ".join(w for w in s.split() if w not in ("the", "a", "an", "is", "are", "of", "in", "there"))


def vqa_match(pred, gold):
    p, g = norm(pred), norm(gold)
    if not p or not g:
        return False
    if p == g or g in p or p in g:
        return True
    yes = {"yes", "no"}
    if g in yes or p.split()[0] in yes:
        return p.split()[0] == g
    return False


def bleu(cands, refs, n=4):
    """Corpus BLEU-n with +1 smoothing, no external deps."""
    def ngrams(toks, k):
        return collections.Counter(tuple(toks[i:i + k]) for i in range(len(toks) - k + 1))
    logp, c_len, r_len = 0.0, 0, 0
    for k in range(1, n + 1):
        match = total = 0
        for c, r in zip(cands, refs):
            ct, rt = norm(c).split(), norm(r).split()
            cn, rn = ngrams(ct, k), ngrams(rt, k)
            match += sum(min(v, rn[g]) for g, v in cn.items())
            total += max(sum(cn.values()), 0)
        logp += math.log((match + 1) / (total + 1)) / n
    for c, r in zip(cands, refs):
        c_len += len(norm(c).split())
        r_len += len(norm(r).split())
    bp = 1.0 if c_len > r_len else math.exp(1 - r_len / max(c_len, 1))
    return bp * math.exp(logp)


def main():
    s = json.load(open(f"{ROOT}/sample.json"))
    ok, n = collections.Counter(), collections.Counter()
    wrong = []
    for i, r in enumerate(s["vqa"]):
        img = gc.load_image(f"{ROOT}/images_sample/{r['image_id']}")
        pred = gc._call_geochat(img, r["question"] + " Answer the question using a single word or phrase.")
        hit = vqa_match(pred, r["ground_truth"])
        ok[r["type"]] += hit
        n[r["type"]] += 1
        if not hit and len(wrong) < 15:
            wrong.append((r["type"], r["question"][:80], r["ground_truth"][:30], pred.strip()[:40]))
        if i % 50 == 0:
            print(f"vqa {i}/{len(s['vqa'])}")

    cands, refs = [], []
    for i, r in enumerate(s["cap"]):
        img = gc.load_image(f"{ROOT}/images_sample/{r['image_id']}")
        cands.append(gc._call_geochat(img, "Describe the image in detail."))
        refs.append(r["ground_truth"])
    b1, b4 = bleu(cands, refs, 1), bleu(cands, refs, 4)

    total = sum(n.values())
    lines = [f"# GeoChat-7B 4-bit zero-shot on VRSBench val sample ({total} VQA, {len(cands)} captions)\n",
             "## VQA", "", "| type | n | accuracy |", "|---|---|---|"]
    for t in sorted(n):
        lines.append(f"| {t} | {n[t]} | {100 * ok[t] / n[t]:.1f}% |")
    lines.append(f"| **all** | {total} | **{100 * sum(ok.values()) / total:.1f}%** |")
    lines += ["", "## Captioning", "", f"BLEU-1 {b1:.3f}, BLEU-4 {b4:.3f} (single reference, {len(cands)} images)", "",
              "Example:", "", f"- model: {cands[0].strip()[:300]}", f"- reference: {refs[0][:300]}", "",
              "## Sample of wrong VQA answers", "", "| type | question | gold | model |", "|---|---|---|---|"]
    lines += [f"| {t} | {q} | {g} | {p} |" for t, q, g, p in wrong]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:20]))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
