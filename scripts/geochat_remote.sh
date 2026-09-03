#!/usr/bin/env bash
# Optional: run GeoChat on your own GPU machine over ssh instead of Colab.
# Set GPU_BOX (user@host) and GPU_REPO (path of this repo there, with a
# .venv-geochat that has the GeoChat deps and ~/GeoChat cloned).
#   GPU_BOX=user@host scripts/geochat_remote.sh start | stop | status
set -e
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin:$PATH"   # some shells lose the system tools
BOX="${GPU_BOX:?set GPU_BOX=user@host}"
REMOTE_DIR="${GPU_REPO:-~/satquery}"
PORT=5000

case "${1:-status}" in
  start)
    ssh "$BOX" "cd $REMOTE_DIR && pgrep -f serve_geochat >/dev/null || (PYTHONPATH=\$HOME/GeoChat:\$PWD GEOCHAT_BACKEND=local nohup .venv-geochat/bin/python scripts/serve_geochat.py --port $PORT > /tmp/geochat_serve.log 2>&1 &)"
    pgrep -f "ssh -N -L $PORT:localhost:$PORT" >/dev/null || (ssh -o ServerAliveInterval=30 -N -L $PORT:localhost:$PORT "$BOX" &)
    echo -n "waiting for model"
    for _ in $(seq 1 60); do curl -s -m 3 "http://localhost:$PORT/health" >/dev/null 2>&1 && break; echo -n .; sleep 5; done
    echo; curl -s "http://localhost:$PORT/health"; echo
    ;;
  stop)
    ssh "$BOX" "pkill -f serve_geochat || true"
    pkill -f "ssh -N -L $PORT:localhost:$PORT" || true
    echo "stopped server and tunnel"
    ;;
  status)
    ssh "$BOX" "pgrep -af serve_geochat || echo 'server not running'; nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader"
    pgrep -f "ssh -N -L $PORT:localhost:$PORT" >/dev/null && echo "tunnel up" || echo "tunnel down"
    ;;
esac
