#!/usr/bin/env bash
# Brings up the demo on this laptop: API on :8000 and the web app on :5173.
# First run also creates the Python venv and installs frontend packages.
# Works on macOS, Linux and Windows (run it from Git Bash).
#
#   scripts/run_demo.sh          start (uses COLAB_URL below unless GEOCHAT_ENDPOINT is set)
#   scripts/run_demo.sh stop
#
# Own GPU machine instead of Colab: GPU_BOX=user@host scripts/run_demo.sh

# >>> CHANGE THIS when the Colab runtime restarts: section 2 of
# >>> notebooks/geochat_colab.ipynb prints the new https://....trycloudflare.com URL
COLAB_URL="https://analyses-lucas-bedroom-listening.trycloudflare.com"

set -e
export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"   # some shells lose the system tools
cd "$(dirname "$0")/.."

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) WINDOWS=1; VENV_BIN=.venv/Scripts ;;
  *)                    WINDOWS=0; VENV_BIN=.venv/bin ;;
esac

# kill whatever listens on a port, on any OS
kill_port() {
  if [ "$WINDOWS" = 1 ]; then
    for pid in $(netstat -ano 2>/dev/null | grep ":$1 " | grep LISTENING | awk '{print $5}' | sort -u); do
      taskkill //PID "$pid" //F >/dev/null 2>&1 || true
    done
  else
    lsof -ti ":$1" 2>/dev/null | xargs kill -9 2>/dev/null || true
  fi
}

if [ "${1:-}" = "stop" ]; then
  kill_port 8000
  kill_port 5173
  [ -n "${GPU_BOX:-}" ] && scripts/geochat_remote.sh stop
  echo "stopped"
  exit 0
fi

# newest python 3.10+ we can find (macOS ships an old /usr/bin/python3, Windows exposes py/python)
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 python "py -3"; do
  if $c -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "need python 3.10 or newer (install from python.org, tick 'Add to PATH')"; exit 1; }

# one-time setup
if [ ! -f "$VENV_BIN/uvicorn" ] && [ ! -f "$VENV_BIN/uvicorn.exe" ]; then
  echo "setting up python venv with $PY (first run only)..."
  $PY -m venv .venv
  "$VENV_BIN/python" -m pip install -q --upgrade pip
  "$VENV_BIN/python" -m pip install -q -r requirements.txt
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

# always restart both servers so nothing stale (old URL, mock mode) lingers
kill_port 8000
kill_port 5173
sleep 1
(PYTHONPATH=. nohup "$VENV_BIN/python" -m uvicorn backend.api.main:app --port 8000 > /tmp/iridis_api.log 2>&1 &)
for _ in $(seq 1 30); do curl -s -m 2 http://localhost:8000/health >/dev/null && break; sleep 1; done
echo "api: $(curl -s http://localhost:8000/health)"

(cd frontend && VITE_USE_MOCK=false nohup npm run dev -- --host 127.0.0.1 > /tmp/iridis_vite.log 2>&1 &)
sleep 3
echo "web app: http://127.0.0.1:5173   (logs: /tmp/iridis_api.log, /tmp/iridis_vite.log)"
