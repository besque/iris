"""API for the web app. Run from the repo root:
    GEOCHAT_ENDPOINT=http://localhost:5000 .venv/bin/uvicorn backend.api.main:app --port 8000
The Vite dev server proxies /api/* here with the prefix stripped."""

import json
import os
import time
import uuid

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from backend.agent.controller import handle_query
from backend.preprocessing.validator import to_rgb, validate_inputs
from backend.reporting.overlay import PALETTES, draw_boxes, draw_mask

UPLOADS = os.environ.get("UPLOAD_DIR", "data/uploads")
URL_PREFIX = os.environ.get("FILES_URL_PREFIX", "/api/files")
os.makedirs(UPLOADS, exist_ok=True)

app = FastAPI(title="iridis AI")
app.mount("/files", StaticFiles(directory=UPLOADS), name="files")
SESSIONS: dict[str, dict] = {}


class QueryIn(BaseModel):
    session_id: str
    query: str


def _preview(path: str, out_png: str) -> Image.Image:
    img = Image.fromarray(to_rgb(path)) if path.lower().endswith((".tif", ".tiff")) else Image.open(path).convert("RGB")
    img.save(out_png)
    return img


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file_0: UploadFile = File(...), file_1: UploadFile | None = File(None)):
    sid = uuid.uuid4().hex[:12]
    sdir = os.path.join(UPLOADS, sid)
    os.makedirs(sdir, exist_ok=True)
    paths, previews, names = [], [], []
    for i, f in enumerate(x for x in (file_0, file_1) if x is not None):
        path = os.path.join(sdir, f"{i}_{os.path.basename(f.filename)}")
        with open(path, "wb") as fh:
            fh.write(await f.read())
        paths.append(path)
        names.append(f.filename)
        try:
            _preview(path, os.path.join(sdir, f"preview_{i}.png"))
            previews.append(f"{URL_PREFIX}/{sid}/preview_{i}.png")
        except Exception as e:  # unreadable file, validation below reports it
            previews.append("")
            names[-1] = f"{f.filename} (unreadable: {e})"

    try:
        validated = validate_inputs(paths)
        compatible, warnings = True, validated["warnings"]
        input_type = validated["config_type"]
        modalities = [img["modality"] for img in validated["images"]]
    except ValueError as e:
        validated, compatible, warnings = None, False, [str(e)]
        input_type = "single_optical" if len(paths) == 1 else "bitemporal_pair"
        modalities = []

    SESSIONS[sid] = {"paths": paths, "validated": validated, "dir": sdir, "queries": 0}
    return {
        "session_id": sid,
        "validation": {
            "input_type": input_type,
            "modalities": modalities,
            "compatible": compatible,
            "warnings": warnings,
            "preview_urls": previews,
            "file_count": len(paths),
            "filenames": names,
        },
    }


@app.post("/query")
def query(body: QueryIn):
    s = SESSIONS.get(body.session_id)
    if not s:
        raise HTTPException(404, "unknown session, upload again")
    if not s["validated"]:
        raise HTTPException(400, "inputs failed validation")

    t0 = time.time()
    try:
        r = handle_query(body.query, s["validated"])
    except Exception as e:
        raise HTTPException(500, f"agent failed: {e}")
    latency = int((time.time() - t0) * 1000)
    trace = r["trace"]
    s["queries"] += 1
    n = s["queries"]

    # evidence goes on the most recent image (the "after" image for pairs)
    base = Image.open(os.path.join(s["dir"], f"preview_{len(s['paths']) - 1}.png"))
    spatial, evidence_url = None, None
    sp = r.get("spatial")
    if sp and sp.get("type") == "bbox" and sp.get("data"):
        w, h = base.size
        boxes = [{"label": trace["task_selected"], "x": x1 / w, "y": y1 / h, "w": (x2 - x1) / w, "h": (y2 - y1) / h}
                 for x1, y1, x2, y2 in sp["data"]]
        img = draw_boxes(base, sp["data"])
        spatial = {"boxes": boxes, "overlay_note": f"{len(boxes)} region(s) found"}
    elif sp and sp.get("type") == "mask" and sp.get("data") is not None:
        mask = np.asarray(sp["data"])
        palette = PALETTES["fusion" if trace["task_selected"] == "fusion" else "change"]
        img = draw_mask(base, mask, palette)
        Image.fromarray((mask > 0).astype(np.uint8) * 255).save(os.path.join(s["dir"], f"mask_{n}.png"))
        note = ("blue = water, orange = built-up" if trace["task_selected"] == "fusion"
                else f"red = changed area ({float(100 * (mask > 0).mean()):.1f}% of scene)")
        spatial = {"mask_url": f"{URL_PREFIX}/{body.session_id}/mask_{n}.png", "overlay_note": note}
    else:
        img = base
    img.save(os.path.join(s["dir"], f"evidence_{n}.png"))
    evidence_url = f"{URL_PREFIX}/{body.session_id}/evidence_{n}.png"

    tools_used = []
    for tool, out in zip(trace["tools_used"], trace["outputs"]):
        tools_used.append({"tool": tool["name"], "params": _jsonable(tool["params"]), "status": "ok",
                           "summary": (out.get("text") or "")[:160]})
    return {
        "answer": r["answer"],
        "spatial": spatial,
        "confidence": r["confidence"],
        "evidence_image_url": evidence_url,
        "trace": {
            "task": trace["task_selected"],
            "input_type": trace["input_config"],
            "tools_used": tools_used,
            "latency_ms": latency,
            "notes": [f"routing: {trace['routing_method']}"] + list(s["validated"]["warnings"]),
        },
    }


@app.post("/report")
def report(payload: dict):
    body = {"generated_by": "iridis AI", **payload}
    return Response(json.dumps(body, indent=2, default=str), media_type="application/json",
                    headers={"Content-Disposition": "attachment; filename=iridis-report.json"})


def _jsonable(x):
    return json.loads(json.dumps(x, default=str))
