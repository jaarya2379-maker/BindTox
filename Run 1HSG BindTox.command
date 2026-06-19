#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8501}"
API_URL="http://$API_HOST:$API_PORT/health"
APP_URL="http://127.0.0.1:$APP_PORT"
API_PID=""
APP_PID=""

cleanup() {
  if [[ -n "$APP_PID" ]]; then
    kill "$APP_PID" 2>/dev/null || true
  fi
  if [[ -n "$API_PID" ]]; then
    kill "$API_PID" 2>/dev/null || true
  fi
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-30}"
  local delay="${3:-1}"

  for ((i=1; i<=attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done

  return 1
}

trap cleanup EXIT INT TERM

cd "$ROOT_DIR"

PYTHONPATH=src ./.venv/bin/python -m bindtox.cli serve-api --host "$API_HOST" --port "$API_PORT" &
API_PID=$!

if ! wait_for_url "$API_URL" 30 1; then
  echo "Backend API did not start at $API_URL"
  exit 1
fi

./start_app.sh &
APP_PID=$!

if ! wait_for_url "$APP_URL" 30 1; then
  echo "Streamlit app did not start at $APP_URL"
  exit 1
fi

if command -v open >/dev/null 2>&1; then
  open "$APP_URL"
else
  echo "Open this URL in your browser: $APP_URL"
fi

wait "$APP_PID"
