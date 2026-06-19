#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

API_HOST="0.0.0.0"
API_PORT="8000"
UI_PORT="8501"

PYTHON_CMD="python3"

NGROK_BIN="$(command -v ngrok || true)"

BACKEND_PID=""
UI_PID=""
NGROK_PID=""

cleanup() {
  echo "Stopping processes..."
  if [[ -n "$NGROK_PID" ]]; then
    kill "$NGROK_PID" 2>/dev/null || true
  fi
  if [[ -n "$UI_PID" ]]; then
    kill "$UI_PID" 2>/dev/null || true
  fi
  if [[ -n "$BACKEND_PID" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "Starting backend on $API_HOST:$API_PORT..."
PYTHONPATH=src $PYTHON_CMD -c "import uvicorn; uvicorn.run('bindtox.backend_api:app', host='$API_HOST', port=$API_PORT)" &
BACKEND_PID=$!

sleep 1

echo "Starting Streamlit UI on 0.0.0.0:$UI_PORT (pointing at backend localhost)..."
# Prefer virtualenv python if present
if [ -x ".venv/bin/python" ]; then
  STREAMLIT_PY=".venv/bin/python -m streamlit"
else
  STREAMLIT_PY="streamlit"
fi
env PYTHONPATH=src BINDTOX_API_URL="http://127.0.0.1:$API_PORT" $STREAMLIT_PY run streamlit_app.py --server.address 0.0.0.0 --server.port $UI_PORT &
UI_PID=$!
UI_PID=$!

sleep 2

if [[ -n "$NGROK_BIN" ]]; then
  echo "ngrok found at $NGROK_BIN — starting tunnel for port $UI_PORT"
  # start ngrok and ask for a public URL
  "$NGROK_BIN" http $UI_PORT --log=stdout > /tmp/ngrok.log 2>&1 &
  NGROK_PID=$!

  # wait for ngrok local API
  for i in {1..15}; do
    if curl -sS http://127.0.0.1:4040/api/tunnels >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  # fetch public URL
  TUNNELS_JSON=$(curl -sS http://127.0.0.1:4040/api/tunnels || true)
  if [[ -n "$TUNNELS_JSON" ]]; then
    PUB_URL=$(echo "$TUNNELS_JSON" | python3 -c "import sys, json; j=json.load(sys.stdin);
print((j.get('tunnels') or [{}])[0].get('public_url',''))")
    if [[ -n "$PUB_URL" ]]; then
      echo "Public URL: $PUB_URL"
      echo "Share this URL with others to let them use the Streamlit UI."
    else
      echo "Could not determine ngrok public URL from API response. Check /tmp/ngrok.log for details." >&2
    fi
  else
    echo "ngrok local API did not respond; check /tmp/ngrok.log" >&2
  fi
else
  echo "ngrok not found. Install ngrok and set up an auth token to expose the UI publicly."
  echo "See: https://ngrok.com/download"
  echo "Or use SSH reverse tunnel: ssh -R 80:localhost:$UI_PORT user@remote-host" 
  echo "You can still share on your LAN at: http://$(ipconfig getifaddr en0 2>/dev/null || echo 'localhost'):$UI_PORT"
fi

echo "Processes running. Press Ctrl-C to stop and clean up." 
wait
