"""How well does the classical change map separate changed vs unchanged pairs?
Runs on LEVIR-CC test pairs, no model needed.
Usage: .venv/bin/python scripts/eval_change_map.py [n_per_class]"""

import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.change.change_map import change_map  # noqa: E402

ROOT = "data/levir_cc"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
NO_CHANGE = ("no change", "no difference", "same", "identical", "nothing has changed", "unchanged")


def is_unchanged(item):
    return any(k in item["sentences"][0]["raw"].lower() for k in NO_CHANGE)


def main():
    items = [i for i in json.load(open(f"{ROOT}/LevirCCcaptions.json"))["images"] if i["filepath"] == "test"]
    unchanged = [i for i in items if is_unchanged(i)][:N]
    changed = [i for i in items if not is_unchanged(i)][:N]

    for method in ("intensity", "edges"):
        pct = {"unchanged": [], "changed": []}
        for label, group in (("unchanged", unchanged), ("changed", changed)):
            for it in group:
                a = Image.open(f"{ROOT}/images/test/A/{it['filename']}")
                b = Image.open(f"{ROOT}/images/test/B/{it['filename']}")
                pct[label].append(change_map(a, b, method=method)["percent"])
        u, c = np.array(pct["unchanged"]), np.array(pct["changed"])
        # best single cut-off and its accuracy
        best = max(((((u < t).sum() + (c >= t).sum()) / (len(u) + len(c)), t)
                    for t in np.arange(0.5, 40, 0.5)))
        print(f"{method:10s} unchanged: median {np.median(u):5.1f}%  p90 {np.percentile(u, 90):5.1f}%   "
              f"changed: median {np.median(c):5.1f}%  p10 {np.percentile(c, 10):5.1f}%   "
              f"best cut {best[1]:.1f}% -> accuracy {100 * best[0]:.0f}%")


if __name__ == "__main__":
    main()
