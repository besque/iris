"""Serves the model over HTTP with the same protocol as the notebook's serve
cell, so the laptop can use GEOCHAT_BACKEND=http through an ssh port forward.

On the GPU box:   GEOCHAT_BACKEND=local python scripts/serve_geochat.py --port 5000
On the laptop:    ssh -N -L 5000:localhost:5000 user@gpu-box   (separate terminal)
                  GEOCHAT_ENDPOINT=http://localhost:5000 .venv/bin/python scripts/test_single_image_tools.py"""

import argparse
import base64
import io
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import geochat_backend as gc  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            self._send(200, {"ok": True, "model": gc.model_name(), "coord_scale": gc.coord_scale()})
        else:
            self._send(404, {"error": "use GET /health or POST /answer"})

    def do_POST(self):
        if self.path.rstrip("/") != "/answer":
            return self._send(404, {"error": "use POST /answer"})
        from PIL import Image
        try:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            image = Image.open(io.BytesIO(base64.b64decode(data["image"]))).convert("RGB")
            text = gc._call_geochat(image, data["prompt"])
            print(f"{data['prompt'][:60]!r} -> {text[:80]!r}", flush=True)
            self._send(200, {"text": text, "model": gc.model_name(), "coord_scale": gc.coord_scale()})
        except Exception as e:  # report to the caller, keep serving
            print("ERROR:", type(e).__name__, e, flush=True)
            self._send(500, {"error": f"{type(e).__name__}: {e}"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to expose beyond localhost")
    args = ap.parse_args()
    if gc.backend_name() == "http":
        sys.exit("this machine should load the model itself: set GEOCHAT_BACKEND=local or qwen")

    print(f"backend {gc.backend_name()}, model {gc.model_name()}, warming up...", flush=True)
    from PIL import Image
    gc._call_geochat(Image.new("RGB", (64, 64)), "What is shown in this image?")
    print(f"model loaded. serving on http://{args.host}:{args.port}  (GET /health, POST /answer)", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
