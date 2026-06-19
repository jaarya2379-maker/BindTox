# BindTox Setup Guide

This guide is for running the project on another laptop from a fresh start.

## What To Send

Send the full `Playground` folder or the generated share ZIP.

Recommended:

```bash
./prepare_share_zip.sh
```

That creates a portable ZIP inside `dist/`.

## Requirements

- Python 3.10 or newer
- Internet access for installing Python packages
- A compatible operating system for the bundled `tools/vina` binary

Note:

- The included `tools/vina` binary is built for macOS Apple Silicon.
- If the other laptop is Windows, Linux, or Intel-only macOS, replace `tools/vina` with the correct AutoDock Vina binary for that machine.

## First-Time Setup

Open Terminal in the project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Start The App

On macOS:

```bash
zsh "Run 1HSG BindTox.command"
```

If the launcher does not open a browser automatically, open:

- `http://127.0.0.1:8501` (local)
	Note: to serve the backend to other machines, start it with --host 0.0.0.0 and point the UI to the backend using the BINDTOX_API_URL environment variable if needed.

## Manual Startup

If the launcher script does not work, use two terminals.

Terminal 1:

```bash
source .venv/bin/activate
PYTHONPATH=src python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000
Or, to run the UI against a remote backend:
BINDTOX_API_URL="http://<backend-host>:8000" streamlit run streamlit_app.py
```

Terminal 2:

```bash
source .venv/bin/activate
./start_app.sh
```

## Portable Project Notes

- Built-in receptor files are stored in `data/receptors/`.
- The app no longer depends on your personal Desktop path.
- Previous run history is stored in `artifacts/bindtox.sqlite3`.
- Models are stored in `models/`.

## Common Problems

`ModuleNotFoundError` or missing packages:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

`vina` fails to run:

- Replace `tools/vina` with the correct binary for that laptop.
- Make sure it is executable:

```bash
chmod +x tools/vina
```

Streamlit or backend does not start:

- Make sure port `8000` and `8501` are free.
- Run the manual startup commands above to see the exact error.
