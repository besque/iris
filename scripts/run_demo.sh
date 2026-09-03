#!/usr/bin/env bash
# Brings up the demo on this laptop: API on :8000 and the web app on :5173.
# First run also creates the Python venv and installs frontend packages.
#
#   scripts/run_demo.sh          start (uses COLAB_URL below unless GEOCHAT_ENDPOINT is set)
#   scripts/run_demo.sh stop
#
# Own GPU machine instead of Colab: GPU_BOX=user@host scripts/run_demo.sh

# >>> CHANGE THIS when the Colab runtime restarts: section 2 of
# >>> notebooks/geochat_colab.ipynb prints the new https://....trycloudflare.com URL
COLAB_URL="https://carb-pilot-buys-empire.trycloudflare.com"

set -e
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin:$PATH"   # some shells lose the system tools
cd "$(dirname "$0")/.."

if [ "${1:-}" = "stop" ]; then
  pkill -f "uvicorn backend.api.main" || true
  pkill -f "vite" || true
  [ -n "${GPU_BOX:-}" ] && scripts/geochat_remote.sh stop
  exit 0
fi

# one-time setup
if [ ! -x .venv/bin/uvicorn ]; then
  echo "setting up python venv (first run only)..."
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
if [ ! -d frontend/node_modules ]; then
  echo "installing frontend packages (first run only)..."
  (cd frontend && npm install --silent)
fi

if [ -z "${GEOCHAT_ENDPOINT:-}" ]; then
  if [ -n "${GPU_BOX:-}" ]; then
    scripts/geochat_remote.sh start
    export GEOCHAT_ENDPOINT=http://localhost:5000
  else
    export GEOCHAT_ENDPOINT="$COLAB_URL"
  fi
fi
export GEOCHAT_ENDPOINT="${GEOCHAT_ENDPOINT%/}"   # a trailing slash would give //health
HEALTH=$(curl -s -m 10 "$GEOCHAT_ENDPOINT/health" || true)
if [ -n "$HEALTH" ]; then
  echo "geochat: $GEOCHAT_ENDPOINT -> $HEALTH"
else
  echo "geochat: $GEOCHAT_ENDPOINT is NOT reachable. The Colab runtime probably restarted:"
  echo "  re-run section 2 of notebooks/geochat_colab.ipynb, then put the new URL in COLAB_URL at the top of this script."
  echo "  Continuing anyway: only the fusion tool and the change map will answer."
fi

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
