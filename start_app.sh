#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
STREAMLIT="$ROOT_DIR/.venv/bin/streamlit"
APP_PORT="${APP_PORT:-8501}"

cd "$ROOT_DIR"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Virtual environment not found at $ROOT_DIR/.venv"
  echo "Create it with:"
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  python -m pip install -r requirements.txt"
  exit 1
fi

if [ ! -x "$STREAMLIT" ]; then
  echo "Streamlit is not installed in the virtual environment."
  echo "Run:"
  echo "  source .venv/bin/activate"
  echo "  python -m pip install -r requirements.txt"
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src"
# Allow pointing the UI at a backend via BINDTOX_API_URL
if [ -n "${BINDTOX_API_URL:-}" ]; then
  echo "Using BINDTOX_API_URL=$BINDTOX_API_URL"
fi

exec "$STREAMLIT" run "$ROOT_DIR/streamlit_app.py" --server.address 0.0.0.0 --server.port "$APP_PORT"
