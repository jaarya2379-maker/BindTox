# BindTox Complete - Getting Started Guide

## 🚀 Quick Start (30 seconds)

```bash
cd '/Users/aarya20067/Desktop/BindTox Complete'
./run_app.sh
```

Then open your browser to **http://localhost:8501**

## 📋 What Just Happened?

The startup script automatically:
1. ✅ Set up Python environment variables
2. ✅ Started the backend API on port 8000
3. ✅ Started the Streamlit UI on port 8501
4. ✅ Checked that everything is working
5. ✅ Showed you where to access the application

## 🎨 Using the Web Interface

### Main Features

**1. Docking & Binding Analysis**
   - Enter a drug SMILES or upload a file (SDF, MOL, PDBQT)
   - Choose a protein (use example or upload)
   - Click "Analyze" to run docking simulation
   - Get binding energy and pose visualization

**2. Toxicity Assessment**
   - Automatic prediction for any submitted compound
   - Shows probability of toxicity
   - Includes molecular descriptors (LogP, TPSA, etc.)

**3. Breach Detection**
   - Check if compounds are found in leaked credentials
   - Security audit for sensitive compounds

### Example Workflow

1. **Go to Docking Tab**
2. **Enter SMILES**: `CN1C=NC2=C1C(=O)N(C(=O)N2C)C` (caffeine)
3. **Select Protein**: Choose "1iep_receptorH.pdb" from examples
4. **Click Analyze**
5. **View Results**:
   - Binding energy: -5.81 kcal/mol
   - 3D pose visualization
   - 9 docking poses ranked by energy
   - Toxicity: Non-toxic (78.7%)

## 📡 Using the Backend API

### Health Check
```bash
curl http://localhost:8000/health
```

### Docking Request
```bash
curl -X POST http://localhost:8000/upload-and-analyze \
  -F 'smiles=CC(C)Cc1ccc(cc1)C(C)C(=O)O' \
  -F 'compound_name=ibuprofen' \
  -F 'protein_name=test' \
  -F 'receptor_file=@data/examples/1iep/1iep_receptorH.pdb'
```

### API Documentation
Visit **http://localhost:8000/docs** for interactive API documentation

## 🌐 Network Access

### Local Network (LAN)
Get your machine IP:
```bash
hostname -I | awk '{print $1}'
```

Access from another machine on the same network:
```
http://YOUR_IP:8501
```

### Internet (Public Access)

The system supports ngrok for secure public access:
```bash
ngrok http 8501
```

This creates a public URL accessible from anywhere.

## 📂 Project Structure

```
BindTox Complete/
├── streamlit_app.py          # Web UI
├── src/bindtox/              # Backend code
│   ├── backend_api.py        # FastAPI endpoints
│   ├── docking.py            # AutoDock Vina integration
│   ├── preprocessing.py      # Molecular preprocessing
│   ├── chemistry.py          # RDKit chemistry functions
│   └── ...
├── data/
│   ├── examples/1iep/        # Example ligand/receptor
│   ├── receptors/            # Additional proteins
│   └── toxicity_reference.csv # Toxicity data
├── models/
│   └── toxicity_model.joblib # Pre-trained ML model
├── run_app.sh                # Start script (recommended)
└── tools/vina                # AutoDock Vina binary
```

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501

# Kill it
kill -9 <PID>
```

### Backend Not Responding
```bash
# Check backend logs
tail -f /tmp/bindtox_backend.log
```

### Conda Environment Not Found
```bash
# Verify environment exists
conda env list

# Create if missing
conda create -n bindtox-py310 python=3.10 -y
conda activate bindtox-py310
cd '/Users/aarya20067/Desktop/BindTox Complete'
pip install -e .
```

### Meeko Binaries Not Found
```bash
# Reinstall Meeko with conda
conda install -n bindtox-py310 -c conda-forge meeko -y

# Verify installation
conda run -n bindtox-py310 mk_prepare_ligand.py --help
```

## 📊 Example Compounds to Test

| Compound | SMILES | Expected Binding |
|----------|--------|-----------------|
| Caffeine | `CN1C=NC2=C1C(=O)N(C(=O)N2C)C` | Moderate |
| Aspirin | `CC(=O)Oc1ccccc1C(=O)O` | Strong |
| Ibuprofen | `CC(C)Cc1ccc(cc1)C(C)C(=O)O` | Moderate |
| Codeine | `COc1ccc2c3ccc4OCOC4c3[nH]c2c1` | Strong |

## ✅ Verification Checklist

- [ ] `run_app.sh` is executable (`chmod +x run_app.sh`)
- [ ] Can access http://localhost:8501
- [ ] Can access http://localhost:8000/docs
- [ ] Health check returns 200 OK
- [ ] Can upload and analyze a compound
- [ ] Docking produces binding energy and poses
- [ ] 3D visualization displays correctly

## 🆘 Getting Help

1. **Check logs**: `tail -f /tmp/bindtox_*.log`
2. **Review API docs**: http://localhost:8000/docs
3. **Check backend health**: http://localhost:8000/health
4. **Restart services**: Press Ctrl+C and run `./run_app.sh` again

## 📝 Common Tasks

### Stop the Application
```bash
# If running via run_app.sh
Press Ctrl+C

# Or kill processes
killall python streamlit 2>/dev/null
```

### Clear Artifact Files
```bash
rm -rf artifacts/ /tmp/bindtox_*
./run_app.sh
```

### View Recent Docking Results
```bash
sqlite3 artifacts/bindtox.sqlite3 "SELECT * FROM results ORDER BY run_id DESC LIMIT 5;"
```

### Access Backend API Without UI
```bash
# List available endpoints
curl http://localhost:8000/docs

# Get computation history
curl 'http://localhost:8000/history?database=artifacts/bindtox.sqlite3&limit=10'
```

## 🎓 How BindTox Works

1. **Input**: User submits SMILES/SDF ligand and PDB/PDBQT receptor
2. **Preprocessing**: 
   - Convert to PDBQT format using Meeko
   - Detect binding pocket from receptor structure
3. **Docking**: 
   - Run AutoDock Vina to find binding poses
   - Rank by binding energy (kcal/mol)
4. **Analysis**:
   - Calculate molecular descriptors (LogP, TPSA, etc.)
   - Predict toxicity using machine learning model
   - Check for leaked credentials (if enabled)
5. **Results**: Return binding energy, poses, and predictions

## 🚀 Advanced Usage

### Run via Docker
```bash
docker-compose up -d
```

### Run via Custom Conda Environment
```bash
conda activate my-env
cd '/Users/aarya20067/Desktop/BindTox Complete'
PYTHONPATH=src python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000
```

### Command-Line Interface (CLI)
```bash
# See available commands
python -m bindtox.cli --help

# Run docking via CLI
python -m bindtox.cli dock \
  --receptor data/examples/1iep/1iep_receptor.pdbqt \
  --ligand data/examples/1iep/1iep_ligand.pdbqt
```

---

**Version**: 1.0.0  
**Last Updated**: 2024-06-18  
**Status**: ✅ Production Ready
