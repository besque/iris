#!/usr/bin/env bash
# Brings up the demo on this laptop: API on :8000 and the web app on :5173.
#
# The GeoChat model runs on a free Colab GPU (notebooks/geochat_colab.ipynb,
# section 2 prints a https://....trycloudflare.com URL):
#   GEOCHAT_ENDPOINT=https://xxxx.trycloudflare.com scripts/run_demo.sh
#   scripts/run_demo.sh stop
#
# Own GPU machine instead of Colab: GPU_BOX=user@host scripts/run_demo.sh
set -e
cd "$(dirname "$0")/.."

if [ "${1:-}" = "stop" ]; then
  pkill -f "uvicorn backend.api.main" || true
  pkill -f "vite" || true
  [ -n "${GPU_BOX:-}" ] && scripts/geochat_remote.sh stop
  exit 0
fi

if [ -z "${GEOCHAT_ENDPOINT:-}" ]; then
  if [ -n "${GPU_BOX:-}" ]; then
    scripts/geochat_remote.sh start
    export GEOCHAT_ENDPOINT=http://localhost:5000
  else
    echo "GEOCHAT_ENDPOINT is not set. Start notebooks/geochat_colab.ipynb on Colab, copy the tunnel URL, then:"
    echo "  GEOCHAT_ENDPOINT=https://xxxx.trycloudflare.com scripts/run_demo.sh"
    echo "Continuing without GeoChat: only the fusion tool and the change map will answer."
  fi
fi
[ -n "${GEOCHAT_ENDPOINT:-}" ] && echo "geochat: $GEOCHAT_ENDPOINT -> $(curl -s -m 10 "$GEOCHAT_ENDPOINT/health" || echo unreachable)"

# always restart the API so it picks up the endpoint given on this run
pkill -f "uvicorn backend.api.main" 2>/dev/null || true
sleep 1
(PYTHONPATH=. nohup .venv/bin/uvicorn backend.api.main:app --port 8000 > /tmp/iridis_api.log 2>&1 &)
for _ in $(seq 1 20); do curl -s -m 2 http://localhost:8000/health >/dev/null && break; sleep 1; done
echo "api: $(curl -s http://localhost:8000/health)"

pgrep -f "vite" >/dev/null || \
  (cd frontend && VITE_USE_MOCK=false nohup npm run dev -- --host 127.0.0.1 > /tmp/iridis_vite.log 2>&1 &)
sleep 3
echo "web app: http://127.0.0.1:5173   (logs: /tmp/iridis_api.log, /tmp/iridis_vite.log)"
