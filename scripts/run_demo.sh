#!/usr/bin/env bash
# Brings up the whole demo on this laptop: GeoChat (remote, on demand), API, web app.
#   scripts/run_demo.sh          start everything, then open http://127.0.0.1:5173
#   scripts/run_demo.sh stop     stop everything, including the remote model
set -e
cd "$(dirname "$0")/.."

if [ "${1:-}" = "stop" ]; then
  pkill -f "uvicorn backend.api.main" || true
  pkill -f "vite" || true
  [ -z "${GEOCHAT_ENDPOINT:-}" ] && scripts/geochat_remote.sh stop
  exit 0
fi

# GEOCHAT_ENDPOINT already set (e.g. a Colab tunnel URL) -> use it, skip the GPU box
if [ -z "${GEOCHAT_ENDPOINT:-}" ]; then
  scripts/geochat_remote.sh start
  export GEOCHAT_ENDPOINT=http://localhost:5000
fi
echo "geochat: $GEOCHAT_ENDPOINT -> $(curl -s -m 10 "$GEOCHAT_ENDPOINT/health" || echo unreachable)"

pgrep -f "uvicorn backend.api.main" >/dev/null || \
  (PYTHONPATH=. nohup .venv/bin/uvicorn backend.api.main:app --port 8000 > /tmp/iridis_api.log 2>&1 &)
for _ in $(seq 1 20); do curl -s -m 2 http://localhost:8000/health >/dev/null && break; sleep 1; done
echo "api: $(curl -s http://localhost:8000/health)"

pgrep -f "vite" >/dev/null || \
  (cd frontend && VITE_USE_MOCK=false nohup npm run dev -- --host 127.0.0.1 > /tmp/iridis_vite.log 2>&1 &)
sleep 3
echo "web app: http://127.0.0.1:5173   (logs: /tmp/iridis_api.log, /tmp/iridis_vite.log, box:/tmp/geochat_serve.log)"
