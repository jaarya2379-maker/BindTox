#!/bin/zsh
# Start backend, UI, and ngrok in background and print the public URL.
# Usage: ./tools/start_public_one_liner.sh

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

API_PORT=${API_PORT:-8000}
UI_PORT=${UI_PORT:-8501}
PYTHON=${PYTHON:-python3}

LOGDIR=${LOGDIR:-/tmp/bindtox_demo_logs}
mkdir -p "$LOGDIR"

echo "Starting backend on 0.0.0.0:$API_PORT (logs: $LOGDIR/backend.log)"
nohup env PYTHONPATH=src $PYTHON -c "import uvicorn; uvicorn.run('bindtox.backend_api:app', host='0.0.0.0', port=$API_PORT)" > "$LOGDIR/backend.log" 2>&1 &
sleep 1

echo "Starting Streamlit UI on 0.0.0.0:$UI_PORT (logs: $LOGDIR/ui.log)"
# Prefer virtualenv python if present
if [ -x ".venv/bin/python" ]; then
  PYEXEC=".venv/bin/python"
else
  PYEXEC="$PYTHON"
fi
nohup env PYTHONPATH=src BINDTOX_API_URL="http://127.0.0.1:$API_PORT" "$PYEXEC" -m streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port $UI_PORT > "$LOGDIR/ui.log" 2>&1 &
sleep 2

NGROK_BIN="$(command -v ngrok || true)"
if [[ -z "$NGROK_BIN" ]]; then
  echo "ngrok not found on PATH. Install ngrok to get a public URL."
  echo "Local LAN URL: http://$(ipconfig getifaddr en0 2>/dev/null || echo '127.0.0.1'):$UI_PORT"
  exit 0
fi

echo "Starting ngrok for port $UI_PORT (logs: $LOGDIR/ngrok.log)"
nohup "$NGROK_BIN" http $UI_PORT > "$LOGDIR/ngrok.log" 2>&1 &

for i in {1..15}; do
  sleep 1
  if curl -sS http://127.0.0.1:4040/api/tunnels >/dev/null 2>&1; then
    break
  fi
done

TUNNELS_JSON=$(curl -sS http://127.0.0.1:4040/api/tunnels || true)
PUB_URL=""
if [[ -n "$TUNNELS_JSON" ]]; then
  PUB_URL=$(echo "$TUNNELS_JSON" | $PYTHON - <<'PY'
import sys, json
try:
    j = json.load(sys.stdin)
    tunnels = j.get('tunnels') or []
    if tunnels:
        print(tunnels[0].get('public_url',''))
except Exception:
    pass
PY
)
fi

if [[ -n "$PUB_URL" ]]; then
  echo "Public URL: $PUB_URL"
  echo "Backend: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo '127.0.0.1'):$API_PORT"
else
  echo "Could not determine ngrok public URL. Check $LOGDIR/ngrok.log"
fi

echo "Logs are in $LOGDIR; processes were started with nohup and will continue running after this script exits."
