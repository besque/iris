"""Builds a synthetic S1/S2 pair with a lake and a town, runs the fusion tool.
Usage: .venv/bin/python scripts/test_fusion.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocessing.validator import validate_inputs  # noqa: E402
from backend.tools.fusion.fusion_tool import FusionTool  # noqa: E402
from scripts.make_sample_pair import make_pair  # noqa: E402

# the pair has a lake in the north-west quarter and a town in the south-east
opt_path, sar_path = make_pair("/tmp/satquery_test")
val = validate_inputs([opt_path, sar_path])
print("config:", val["config_type"])
res = FusionTool().run(val["images"], "identify built-up and water regions")
print("answer:", res.text)
print("confidence:", res.confidence)

mask = res.spatial["data"]
water_ok = (mask[:40, :40] == 1).mean()
built_ok = (mask[80:, 80:] == 2).mean()
print(f"water hit rate in lake area: {water_ok:.0%}, built hit rate in town: {built_ok:.0%}")
assert water_ok > 0.9 and built_ok > 0.9, "fusion missed the planted regions"
print("fusion test passed")
