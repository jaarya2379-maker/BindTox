# BindTox — Quick Share Instructions

**Status**: ✅ Clean, optimized, production-ready for sharing

---

## What's Included

- ✅ **Source code** (src/) — all Python modules
- ✅ **Web UI** (streamlit_app.py) — interactive dashboard
- ✅ **REST API** (backend_api.py) — FastAPI endpoints
- ✅ **Docking binary** (tools/vina) — molecular docking engine
- ✅ **Example data** (data/examples/1iep/) — sample receptor/ligand
- ✅ **ML model** (models/toxicity_model.joblib) — toxicity classifier
- ✅ **Docker files** — for containerized deployment
- ✅ **Helper scripts** — for quick setup and sharing

---

## Three Ways to Share

### 1️⃣ **Local (single machine)**

Perfect for: **Personal testing, local laptop**

```bash
# Terminal 1: Backend
export PYTHONPATH=src
python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000

# Terminal 2: UI
./start_app.sh
```

Then open: **http://localhost:8501**

---

### 2️⃣ **Local Network (LAN)**

Perfect for: **Team on same Wi-Fi**

**Machine A (backend):**
```bash
export PYTHONPATH=src
python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000
```

**Machine B (UI):**
```bash
# Replace 192.168.1.10 with Machine A's IP
export BINDTOX_API_URL="http://192.168.1.10:8000"
./start_app.sh
```

Find Machine B's IP and share: **http://machine-b-ip:8501**

**How to find IPs:**
- **macOS/Linux**: `ifconfig | grep inet`
- **Windows**: `ipconfig`

---

### 3️⃣ **Public Internet (ngrok)**

Perfect for: **Demo to collaborators anywhere, quick proof-of-concept**

```bash
./tools/expose_with_ngrok.sh
```

Will print public URL like: `https://abc-def-123.ngrok-free.dev`

Share that link with anyone to access your UI.

**Requirements:**
- ngrok installed (brew install --cask ngrok)
- (Optional) ngrok authtoken for longer tunnels

**Limitations:**
- Free ngrok has IP rate limits (OK for demos)
- For production: use Docker + cloud server instead

---

### 4️⃣ **Docker (any machine)**

Perfect for: **Production-ready, easy deployment**

```bash
docker compose up --build
```

Access:
- Backend API: http://localhost:8000/docs
- UI Dashboard: http://localhost:8501

---

## Setup Steps (5 min)

### 1. Install dependencies

```bash
# Option A: Conda (recommended, includes chemistry libs)
conda create -n bindtox python=3.10
conda activate bindtox
conda install -c conda-forge rdkit openbabel
pip install -r requirements.txt
pip install -e .

# Option B: Pip only
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 2. Choose a deployment method (above)

---

## Troubleshooting

### Port already in use
```bash
# Kill existing processes
lsof -ti:8000 | xargs kill -9    # backend
lsof -ti:8501 | xargs kill -9    # UI
```

### Chemistry warnings
Install RDKit (optional but recommended):
```bash
conda install -c conda-forge rdkit
```

### ngrok not installed
```bash
brew install --cask ngrok
# Then add authtoken from https://dashboard.ngrok.com
ngrok config add-authtoken YOUR_TOKEN
```

### Docking fails ("No ligand preparation binary found")
```bash
conda install -c conda-forge meeko openbabel
```

---

## What Users Need to Know

- **Python 3.10+** required
- **No cloud account needed** for LAN/local use
- **ngrok account optional** (free tier works for quick demos)
- **Docker recommended** for production deployment
- **~3 GB RAM** recommended for docking
- **Works on**: macOS (ARM64 + Intel), Linux, Windows

---

## File Summary

| Item | Size | Purpose |
|------|------|---------|
| src/bindtox/ | 150 KB | Core package |
| streamlit_app.py | 32 KB | Web dashboard |
| data/examples/ | 1.2 MB | Sample inputs |
| models/ | 300 KB | ML toxicity model |
| tools/vina | 1.1 MB | Docking binary |
| Total | **2.9 MB** | Minimal, shareable |

---

## Getting Help

1. Check **README.md** for full documentation
2. Check **SETUP_GUIDE.md** for advanced setup
3. Run tests: `PYTHONPATH=src python -m pytest tests/`
4. View API docs (when backend running): http://localhost:8000/docs

---

## Next Steps

**To share:**

1. Zip or share this folder (2.9 MB)
2. Users follow **Quick Start** above
3. Choose deployment method (local/LAN/public)
4. Done! 🎉

**To develop:**

1. Make changes in `src/bindtox/`
2. Run tests locally
3. Test on LAN
4. Deploy via Docker when ready

---

**BindTox** — drug discovery toolkit, now ready for teams everywhere.
