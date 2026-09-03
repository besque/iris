"""Runs one example query per task through the controller and prints the responses.
Usage: PYTHONPATH=. python scripts/run_controller_demo.py"""

import json

from backend.agent.controller import handle_query

EXAMPLES = [
    ("Describe the land-cover and major objects visible in this image.",
     {"config_type": "single_optical", "images": ["a.png"], "warnings": []}),
    ("Highlight the water body referred to in the query.",
     {"config_type": "single_optical", "images": ["a.png"], "warnings": []}),
    ("How many buildings are near the river?",
     {"config_type": "single_optical", "images": ["a.png"], "warnings": []}),
    ("What changed between these two dates, and where did the change occur?",
     {"config_type": "bitemporal_pair", "images": ["t1.png", "t2.png"], "warnings": []}),
    ("Use the optical and SAR images together to identify built-up and water-covered regions.",
     {"config_type": "crossmodal_pair", "images": ["opt.tif", "sar.tif"], "warnings": []}),
]

for query, inputs in EXAMPLES:
    resp = handle_query(query, inputs)
    print(f"\nQ: {query}")
    print(f"   task={resp['trace']['task_selected']}  routing={resp['trace']['routing_method']}  conf={resp['confidence']}")
    print(f"   A: {resp['answer']}")
    print(f"   trace: {json.dumps(resp['trace']['tools_used'])}")
