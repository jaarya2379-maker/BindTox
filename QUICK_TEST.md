# BindTox Complete - Quick Verification Test

## ✅ Pre-Test Checklist
- [ ] Services running (`./run_app.sh` started or backend + streamlit running)
- [ ] Backend responding on port 8000
- [ ] Streamlit UI responding on port 8501

## 🧪 Test 1: Health Check
```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{"status":"ok"}
```

**Result:** ______________________

## 🧪 Test 2: API Documentation
**URL:** http://localhost:8000/docs

**Expected:** 
- FastAPI Swagger UI loads
- Endpoints visible (upload-and-analyze, history, etc.)
- Green "try it out" buttons available

**Result:** ______________________

## 🧪 Test 3: Streamlit Web Interface
**URL:** http://localhost:8501

**Expected:**
- BindTox Complete dashboard loads
- Sidebar with "Docking" and other tabs visible
- Can upload/paste SMILES compounds

**Result:** ______________________

## 🧪 Test 4: Complete Docking Test (CLI)
```bash
curl -X POST http://localhost:8000/upload-and-analyze \
  -F 'smiles=CN1C=NC2=C1C(=O)N(C(=O)N2C)C' \
  -F 'compound_name=caffeine_test' \
  -F 'protein_name=1iep' \
  -F 'receptor_file=@data/examples/1iep/1iep_receptorH.pdb' 2>&1 | python -m json.tool | head -50
```

**Expected Response:**
- HTTP Status: 200 OK
- Contains "binding_energy": -5.81 (or similar)
- Contains "docking" object with results
- No error messages

**Result:** ______________________

## 🧪 Test 5: Via Streamlit UI
1. Navigate to http://localhost:8501
2. Go to "Docking & Binding Analysis" tab
3. Enter SMILES: `CC(C)Cc1ccc(cc1)C(C)C(=O)O` (ibuprofen)
4. Click "Upload Receptor from Examples" → select "1iep_receptorH.pdb"
5. Click "Run Docking Analysis"

**Expected:**
- Analysis completes without errors
- Shows "Binding Energy" value
- Displays molecular properties
- 3D visualization appears

**Result:** ______________________

## 📊 Success Criteria

| Test | Status | Notes |
|------|--------|-------|
| Health Check | ✅/❌ | Backend responding |
| API Docs | ✅/❌ | Documentation accessible |
| Streamlit UI | ✅/❌ | Web interface loads |
| CLI Docking | ✅/❌ | **Binding Energy obtained** |
| Web UI Docking | ✅/❌ | End-to-end workflow |

## 🎯 Overall Status

- **All tests passing**: ✅ **READY FOR PRODUCTION**
- **Some tests failing**: ⚠️ See troubleshooting below
- **Major issues**: ❌ Contact support

## 🔧 Quick Troubleshooting

### Backend not responding
```bash
# Check if it's running
ps aux | grep uvicorn

# Check logs
tail -100 /tmp/bindtox_backend.log

# Restart
killall python
cd '/Users/aarya20067/Desktop/BindTox Complete'
PYTHONPATH=src CONDA_PREFIX='/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310' \
  /opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000 &
```

### Streamlit not responding
```bash
# Check if it's running
ps aux | grep streamlit

# Check logs
tail -100 /tmp/bindtox_streamlit.log

# Restart
killall streamlit
cd '/Users/aarya20067/Desktop/BindTox Complete'
CONDA_PREFIX='/opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310' \
  /opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 &
```

### Meeko binaries not found
```bash
# Reinstall
conda install -n bindtox-py310 -c conda-forge meeko -y

# Verify
ls /opt/homebrew/Caskroom/miniforge/base/envs/bindtox-py310/bin/ | grep mk_
```

### Port already in use
```bash
# Find what's using the port
lsof -i :8000  # for backend
lsof -i :8501  # for UI

# Kill the process
kill -9 <PID>
```

## 📋 Notes

- Binding energy values typically range from -3 to -12 kcal/mol
- Negative values indicate favorable binding
- Lower (more negative) values = stronger binding
- Test with different SMILES to verify consistency
- UI should load immediately, docking may take 10-30 seconds

## ✨ What's Been Fixed

1. **Meeko binary discovery** - Now searches conda environment
2. **Environment variables** - PYTHONPATH and CONDA_PREFIX properly set
3. **Python compatibility** - Supports Python 3.10
4. **Package installation** - Editable install with `pip install -e .`
5. **Network binding** - Services bind to 0.0.0.0 for network access
6. **Error handling** - Clear error messages for debugging

## 🚀 Next Steps

Once all tests pass:

1. **Share locally**: Give other machines the IP address
   ```bash
   echo "Access from: http://$(hostname -I | awk '{print $1}'):8501"
   ```

2. **Share publicly**: Use ngrok for internet access
   ```bash
   ngrok http 8501
   ```

3. **Deploy**: Use Docker or systemd for always-on access
   - See GETTING_STARTED.md for Docker options
   - Or systemd service files (available on request)

---

**Last Updated:** 2024-06-18  
**BindTox Version:** Complete  
**Test Framework:** Manual verification
