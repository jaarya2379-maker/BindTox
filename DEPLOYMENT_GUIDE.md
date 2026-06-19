# ✅ BindTox — Now Fully Fixed & Network-Ready

## Problem Fixed

✅ **ModuleNotFoundError** — Fixed by properly installing the `bindtox` package

✅ **Python version conflict** — Updated `pyproject.toml` to support Python 3.10

✅ **Import errors** — Package now installs correctly with all dependencies

✅ **Reliable startup** — Created `run_bindtox.sh` script for one-command deployment

---

## Current Status

### 🟢 Services Running

| Service | Port | Status | URL |
|---------|------|--------|-----|
| **Backend API (Uvicorn)** | 8000 | ✅ Running | http://localhost:8000 |
| **Streamlit UI** | 8501 | ✅ Running | http://localhost:8501 |
| **API Docs** | 8000 | ✅ Available | http://localhost:8000/docs |

### 📍 Access From

- **Local Machine**: http://localhost:8501
- **Same Network (LAN)**: http://<your-ip>:8501
- **Public (ngrok)**: ./tools/expose_with_ngrok.sh

---

## How to Start BindTox Reliably

### Method 1: Use the Startup Script (Recommended)

```bash
cd /Users/aarya20067/Desktop/BindTox\ Complete
./run_bindtox.sh
```

This will:
- ✅ Verify Python environment
- ✅ Install/update package
- ✅ Check for port conflicts
- ✅ Start backend and UI
- ✅ Display access URLs
- ✅ Print logs automatically

### Method 2: Manual Start (if needed)

**Terminal 1 - Backend:**
```bash
cd /Users/aarya20067/Desktop/BindTox\ Complete
/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000
```

**Terminal 2 - UI:**
```bash
cd /Users/aarya20067/Desktop/BindTox\ Complete
/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/python -m streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

---

## What Was Fixed

### 1. **Import Error Resolution**

**Problem:** `ModuleNotFoundError: No module named 'bindtox'`

**Solution:** 
- Updated `pyproject.toml` to support Python 3.10 (from 3.11 requirement)
- Package now installs in editable mode: `pip install -e .`
- All imports work without needing `PYTHONPATH=src`

### 2. **Dependency Installation**

Automatically installs/ensures these are present:
- ✅ Meeko — receptor preparation
- ✅ Open Babel — ligand format conversion
- ✅ RDKit — chemistry descriptors
- ✅ Uvicorn — FastAPI server
- ✅ Streamlit — web dashboard
- ✅ AutoDock Vina — docking engine

### 3. **Network Binding**

Both services now bind to `0.0.0.0` (all interfaces):
- ✅ Accessible from localhost
- ✅ Accessible from LAN (same network)
- ✅ Ready for public exposure via ngrok/Docker

### 4. **Robust Startup Script**

`run_bindtox.sh` ensures:
- ✅ No conflicting processes on ports 8000/8501
- ✅ Clean Python environment activation
- ✅ Automatic package installation
- ✅ Health checks before reporting success
- ✅ Helpful log locations
- ✅ Network IP auto-detection

---

## Testing the Setup

### Test Docking (CLI)

```bash
export PYTHONPATH=src  # Not needed anymore, but still works
/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/python -m bindtox.cli dock \
  --receptor data/examples/1iep/1iep_receptor.pdbqt \
  --ligand data/examples/1iep/1iep_ligand.pdbqt \
  --center-x 13.073 --center-y 22.467 --center-z 5.557 \
  --output-dir /tmp/test_dock
```

**Expected output:**
```json
{
  "binding_energy": -3.859,
  "pose_rank": 1,
  ...
}
```

### Test via UI

1. Open http://localhost:8501
2. Select receptor (1HSG or 4HHB)
3. Enter SMILES or upload ligand
4. Click "Run Docking"
5. View binding energy and 3D pose

### Test Backend API

```bash
curl http://localhost:8000/health
# Response: {"status":"ok"}

curl http://localhost:8000/docs
# Response: Interactive API documentation
```

---

## Logs Location

All logs are stored in `/tmp/bindtox_logs/`:

```bash
# View backend logs (requests, errors)
tail -f /tmp/bindtox_logs/backend.log

# View UI logs (Streamlit output)
tail -f /tmp/bindtox_logs/ui.log

# View startup log
cat /tmp/startup.log
```

---

## Troubleshooting

### "Port already in use"

The startup script handles this automatically, but if needed:

```bash
# Kill processes on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill processes on port 8501 (UI)
lsof -ti:8501 | xargs kill -9

# Then run the startup script again
./run_bindtox.sh
```

### "Docking: No ligand preparation binary found"

Install Meeko:
```bash
/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/python -m pip install meeko
```

### "Cannot find bindtox module"

Reinstall the package:
```bash
cd /Users/aarya20067/Desktop/BindTox\ Complete
/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/python -m pip install -e .
```

### "ModuleNotFoundError"

Run the startup script which handles everything:
```bash
./run_bindtox.sh
```

---

## Share on Network

### Local Network (Same Wi-Fi)

1. Start services: `./run_bindtox.sh`
2. Find your IP: `ifconfig | grep "inet " | grep -v 127`
3. Share: http://<your-ip>:8501

**Example:** http://192.168.1.10:8501

### Public (Anywhere on Internet)

```bash
./tools/expose_with_ngrok.sh
```

Will print a public URL like: https://abc-def-123.ngrok-free.dev

---

## Files Modified

- ✅ `pyproject.toml` — Changed Python requirement from >=3.11 to >=3.10
- ✅ `run_bindtox.sh` — New reliable startup script (created)
- ✅ Verified: `streamlit_app.py`, `src/bindtox/__init__.py` — imports now work

---

## Next Steps

### Use It Now

```bash
./run_bindtox.sh
# Then open: http://localhost:8501
```

### Deploy It

```bash
# Option 1: Docker (easiest for production)
docker compose up --build

# Option 2: Public with ngrok
./tools/expose_with_ngrok.sh

# Option 3: LAN share
./run_bindtox.sh  # Get IP, share with team
```

### Develop It

```bash
# Make changes to source code in src/bindtox/
# No need to reinstall, editable mode handles updates automatically
# Restart services: ./run_bindtox.sh
```

---

## Summary

| Aspect | Status |
|--------|--------|
| **Import errors** | ✅ Fixed |
| **Package installation** | ✅ Works |
| **Services startup** | ✅ Reliable |
| **Docking** | ✅ Working |
| **Network access** | ✅ 0.0.0.0 binding |
| **LAN sharing** | ✅ Ready |
| **Public sharing** | ✅ ngrok script ready |
| **Documentation** | ✅ Complete |

---

**BindTox is now fully functional, reliable, and network-ready! 🚀**

Start with: `./run_bindtox.sh` and open http://localhost:8501
