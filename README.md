# BindTox```markdown

# BindTox

**Drug-Protein Binding Affinity and Toxicity Simulator** — computational screening toolkit for drug discovery.

Drug-Protein Binding and Toxicity Simulator for computational screening.

- 🔬 **Molecular Docking**: AutoDock Vina for binding pose and energy prediction

- 🧬 **Toxicity Prediction**: ML-based screening modelSee `SETUP_GUIDE.md` for additional local setup notes.

- 🖥️ **Web UI**: Streamlit dashboard for easy interaction

- 📡 **REST API**: FastAPI backend for programmatic access## Quick start (local)

- 🌐 **Network Ready**: Run locally, on LAN, or expose publicly via ngrok/Docker

```bash

---cd /path/to/BindTox

python3 -m venv .venv

## Quick Start (5 minutes)source .venv/bin/activate

python -m pip install -r requirements.txt

### 1. Install dependenciespython -m pip install -e .

```

**Option A: Using conda (recommended, includes RDKit)**

Run UI:

```bash

conda create -n bindtox python=3.10```bash

conda activate bindtox./start_app.sh

conda install -c conda-forge rdkit openbabel```

pip install -r requirements.txt

pip install -e .Run backend:

```

```bash

**Option B: Using pip (without RDKit chemistry features)**PYTHONPATH=src python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000

```

```bash

python3 -m venv .venvOr set `BINDTOX_API_URL` to point the UI to a backend host:

source .venv/bin/activate  # on Windows: .venv\Scripts\activate

pip install -r requirements.txt```bash

pip install -e .BINDTOX_API_URL="http://192.168.1.10:8000" streamlit run streamlit_app.py

``````



### 2. Start backend and UI (both on your machine)## Run across two machines (LAN example)



Terminal 1 (Backend API):This example shows Machine A running the backend API and Machine B running the Streamlit UI that talks to Machine A.



```bashMachine A (backend):

export PYTHONPATH=src

python -m bindtox.cli serve-api --host 0.0.0.0 --port 80001. Start the backend on Machine A and bind to all interfaces:

```

```bash

Terminal 2 (Streamlit UI):cd /path/to/BindTox

source .venv/bin/activate   # optional, if you created a virtualenv

```bashPYTHONPATH=src python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000

./start_app.sh```

```

Assume Machine A has IP 192.168.1.10 on the local network.

Open your browser to: **http://localhost:8501**

Machine B (UI):

---

1. Start the Streamlit UI on Machine B and point it at Machine A's backend (replace the IP with Machine A's IP):

## Share on Local Network (LAN)

```bash

### Machine A: Start backendcd /path/to/BindTox

```bashsource .venv/bin/activate   # optional

export PYTHONPATH=srcBINDTOX_API_URL="http://192.168.1.10:8000" streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501

python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000```

```

2. Open the UI from anywhere on the same network at:

Find Machine A's IP:

- **macOS/Linux**: `ifconfig | grep "inet "````

- **Windows**: `ipconfig`http://<machine-b-ip>:8501

```

Example: `192.168.1.10`

Notes:

### Machine B: Start UI pointing to Machine A

- If you prefer the UI to run on Machine A, you can run Streamlit there and point it to `http://127.0.0.1:8000`, or run both services in Docker (see below).

```bash- If your network uses firewalls, ensure ports 8000 (backend) and 8501 (UI) are reachable as needed.

export BINDTOX_API_URL="http://192.168.1.10:8000"

./start_app.sh## Docker Compose (quick network-friendly deployment)

```

Additions in this repo:

Find Machine B's IP and share: **http://machine-b-ip:8501**

- `Dockerfile` — small image for running BindTox services

**Note:** Both machines must be on the same network (Wi-Fi/LAN).- `docker-compose.yml` — starts `backend` and `ui` services, exposing ports and wiring `BINDTOX_API_URL` for the UI



---The Compose setup will start two services:



## Share Publicly (via ngrok)- `backend`: FastAPI backend listening on port 8000

- `ui`: Streamlit UI on port 8501 pointing to `http://backend:8000` inside the Compose network

Quick public URL for demos (requires [ngrok](https://ngrok.com)):

Usage:

```bash

./tools/expose_with_ngrok.sh1. Build and start both services:

```

```bash

This will:docker compose up --build

1. Start backend on port 8000```

2. Start Streamlit UI on port 8501

3. Create ngrok tunnel and print public URL2. The backend will be available at `http://localhost:8000` on the host running Docker.

   The UI will be available at `http://localhost:8501` and will be configured to talk to the backend.

Copy and share the printed URL. Others can access it from anywhere on the internet.

3. To make the services reachable on your LAN, ensure Docker host networking and firewall allow incoming connections on ports 8000/8501, or modify `docker-compose.yml` to map ports differently.

**Installation (if ngrok is not installed):**

Customization example (run backend only and point an external UI to it):

```bash

# macOS```bash

brew install --cask ngrok# start only the backend

docker compose up --build backend

# Or download from https://ngrok.com/download

```# on another machine, run the UI and point it at the backend IP

BINDTOX_API_URL="http://192.168.1.10:8000" streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501

**Note:** For production, use a proper cloud deployment, VPN, or reverse proxy instead of ngrok.```



---If you'd like, I can add an alternate Compose file with persistent volumes for artifacts, and a build target that includes Vina or other binary dependencies.



## Docker Deployment## CLI Usage



### Build and start both servicesSee full CLI usage in `src/bindtox/cli.py` for all commands (descriptors/dock/analyze/train-toxicity/serve-api).



```bash## BreachWatch Backend

docker compose up --build

```This repo also includes a separate simulated dark web monitoring backend under `src/breachwatch`.



Services:See `SETUP_GUIDE.md` for additional setup and notes.

- Backend API: http://localhost:8000/docs

- UI Dashboard: http://localhost:8501## Make the app available to anyone (ngrok helper)



### Customize portsIf you want a very quick way to share the Streamlit UI publicly, run the helper script that starts the backend and UI and opens an ngrok tunnel (if `ngrok` is installed):



Edit `docker-compose.yml` to change port mappings, then rebuild:```bash

./tools/expose_with_ngrok.sh

```bash```

docker compose up --build

```The script will print a public URL (ngrok) that you can share. If `ngrok` is not installed it will fall back to showing your LAN URL.



---Note: for production public access use a secure deployment (reverse proxy, authentication, VPN, or a cloud server). ngrok is great for quick demos and testing.



## CLI CommandsAlternatively, there's a simpler one-line-style helper that starts backend, UI, and ngrok in the background and prints the public URL and log locations:



Run analysis directly from terminal without UI:```bash

./tools/start_public_one_liner.sh

```bash```

# Show molecular descriptors for a compound (SMILES)

export PYTHONPATH=srcIt creates logs under `/tmp/bindtox_demo_logs` by default. You can override ports with `API_PORT` and `UI_PORT` environment variables.

python -m bindtox.cli descriptors --smiles "CCO"

````

# Run docking (receptor PDB, ligand SDF/MOL2)# BindTox

python -m bindtox.cli dock \

  --receptor data/receptors/1HSG.pdb \Drug-Protein Binding and Toxicity Simulator for computational screening.

  --ligand my_ligand.sdf \

  --output-dir ./resultsFor sharing to another laptop, see [SETUP_GUIDE.md](/Users/aarya20067/Documents/Playground/SETUP_GUIDE.md).



# Full end-to-end analysis (SMILES + docking + toxicity)To create a ready-to-send package:

python -m bindtox.cli analyze \

  --smiles "CCO" \```bash

  --receptor-pdb data/receptors/1HSG.pdb \./prepare_share_zip.sh

  --compound-name "Ethanol" \```

  --workspace ./my_analysis

This project is organized around the architecture you described:

# Show recent runs

python -m bindtox.cli history --limit 10- `input_layer`: validates SMILES, ligand files, protein files, and uploads

```- `preprocessing`: prepares proteins and ligands for docking

- `docking`: runs AutoDock Vina and extracts binding energy

---- `binding_analysis`: interprets affinity and likely interaction patterns

- `toxicity`: trains and runs the Toxic / Non-toxic model

## File Structure- `backend_api`: exposes FastAPI endpoints for analysis and uploads

- `ui`: Streamlit dashboard for an easy-to-use front end

```

.Core implementation files:

├── src/bindtox/              # Main package

│   ├── backend_api.py        # FastAPI endpoints- [input_layer.py](/Users/aarya20067/Documents/Playground/src/bindtox/input_layer.py)

│   ├── docking.py            # Vina integration- [preprocessing.py](/Users/aarya20067/Documents/Playground/src/bindtox/preprocessing.py)

│   ├── chemistry.py          # RDKit descriptors- [docking.py](/Users/aarya20067/Documents/Playground/src/bindtox/docking.py)

│   ├── toxicity.py           # ML model- [binding_analysis.py](/Users/aarya20067/Documents/Playground/src/bindtox/binding_analysis.py)

│   ├── orchestrator.py       # Pipeline- [toxicity.py](/Users/aarya20067/Documents/Playground/src/bindtox/toxicity.py)

│   ├── preprocessing.py      # Ligand/receptor prep- [orchestrator.py](/Users/aarya20067/Documents/Playground/src/bindtox/orchestrator.py)

│   ├── input_layer.py        # File validation- [backend_api.py](/Users/aarya20067/Documents/Playground/src/bindtox/backend_api.py)

│   └── cli.py                # CLI commands- [streamlit_app.py](/Users/aarya20067/Documents/Playground/streamlit_app.py)

├── src/breachwatch/          # Dark web monitoring (optional)

├── streamlit_app.py          # Web UI## Install

├── tools/

│   ├── vina                  # AutoDock Vina binary```bash

│   ├── expose_with_ngrok.sh  # Public sharing helpercd /path/to/Playground

│   └── start_public_one_liner.shpython3 -m venv .venv

├── data/source .venv/bin/activate

│   ├── examples/1iep/        # Example receptor/ligandpython -m pip install -r requirements.txt

│   ├── receptors/            # Receptor PDB filespython -m pip install -e .

│   └── toxicity_reference.csv```

├── models/

│   ├── toxicity_model.joblib## Run the UI

│   └── toxicity_model.metadata.json

├── tests/                    # Unit tests```bash

├── Dockerfile                # Container imagecd /path/to/Playground

├── docker-compose.yml        # Multi-service orchestration./start_app.sh

├── requirements.txt          # Python dependencies```

├── pyproject.toml            # Package metadata

└── README.md                 # This fileIf macOS blocks direct execution:

```

```bash

---zsh start_app.sh

```

## Troubleshooting

## Run the Backend API

### "No ligand preparation binary found"

```bash

The backend needs **Meeko**, **AutoDockTools**, or **Open Babel** to convert ligand formats (SDF → PDBQT).cd /path/to/Playground

source .venv/bin/activate

```bashPYTHONPATH=src python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000

# Via condaOr set BINDTOX_API_URL to point the UI to a remote host, e.g.:

conda install -c conda-forge meeko openbabelBINDTOX_API_URL="http://192.168.1.10:8000" streamlit run streamlit_app.py

```

# Or via pip

pip install openbabel-wheelMain API routes:

```

- `GET /health`

### Port already in use- `GET /history`

- `POST /analyze`

Kill existing processes:- `POST /upload-and-analyze`



```bash## CLI Usage

# macOS/Linux

lsof -ti:8000 | xargs kill -9  # backendCalculate descriptors:

lsof -ti:8501 | xargs kill -9  # UI

```bash

# WindowsPYTHONPATH=src python -m bindtox.cli descriptors --smiles "CC(=O)OC1=CC=CC=C1C(=O)O"

netstat -ano | findstr :8000```

taskkill /PID <PID> /F

```Train toxicity model:



### ngrok not found```bash

PYTHONPATH=src python -m bindtox.cli train-toxicity \

Install ngrok:  --dataset data/toxicity_reference.csv \

  --output models/toxicity_model.joblib

```bash```

# macOS

brew install --cask ngrokAnalyze from SMILES and protein:



# Linux/Windows: Download from https://ngrok.com/download```bash

```PYTHONPATH=src python -m bindtox.cli analyze \

  --compound-name Aspirin \

Add your ngrok authtoken (from https://dashboard.ngrok.com/):  --protein-name "Protease Enzyme" \

  --smiles "CC(=O)OC1=CC=CC=C1C(=O)O" \

```bash  --receptor-pdb data/receptors/1HSG.pdb \

ngrok config add-authtoken YOUR_TOKEN_HERE  --model-path models/toxicity_model.joblib \

```  --workspace artifacts/latest_run \

  --database artifacts/bindtox.sqlite3

### Chemistry features disabled (warnings about RDKit)```



RDKit is optional. If not installed, the UI will show warnings but docking-only workflows still work.Analyze from ligand file:



To enable chemistry features:```bash

PYTHONPATH=src python -m bindtox.cli analyze-file \

```bash  --ligand /absolute/path/to/ligand.sdf \

conda install -c conda-forge rdkit  --protein-name "Protease Enzyme" \

```  --receptor-pdb data/receptors/1HSG.pdb \

  --workspace artifacts/file_run \

### Backend returns 500 errors  --database artifacts/bindtox.sqlite3

```

Check backend logs:

Run docking only:

```bash

# If running directly, you'll see errors in terminal```bash

# If using Docker, check logs:PYTHONPATH=src python -m bindtox.cli dock \

docker compose logs backend  --receptor /absolute/path/to/receptor.pdbqt \

  --ligand /absolute/path/to/ligand.pdbqt \

# Or check artifact logs (if created):  --center-x 13.073 --center-y 22.467 --center-z 5.557 \

tail -n 200 /tmp/bindtox_demo_logs/backend.log  --size-x 22 --size-y 22 --size-z 22 \

```  --output-dir artifacts/docking_cli

```

---

## Notes

## API Reference

- `1HSG.pdb` is supported in the workflow and has been verified locally.

### Health check- Built-in receptor files for sharing are stored in `data/receptors/`.

```bash- Binding-site detection prefers co-crystallized ligand coordinates when present.

curl http://localhost:8000/health- If full receptor preparation fails on a difficult structure, the app falls back to a basic rigid-receptor PDBQT writer so docking can still proceed.

```- The bundled toxicity model pipeline reaches about `77.8%` accuracy on the included reference dataset.



### Analyze compound## BreachWatch Backend

```bash

curl -X POST http://localhost:8000/analyze \This repo also now includes a separate simulated dark web monitoring backend under [src/breachwatch](/Users/aarya20067/Documents/Playground/src/breachwatch).

  -H "Content-Type: application/json" \

  -d '{Main pieces:

    "smiles": "CCO",

    "compound_name": "Ethanol",- simulated breach dataset: [data/breachwatch/leaked_credentials.json](/Users/aarya20067/Documents/Playground/data/breachwatch/leaked_credentials.json)

    "protein_name": "1HSG",- FastAPI service: [api.py](/Users/aarya20067/Documents/Playground/src/breachwatch/api.py)

    "workspace": "artifacts/run_1"- risk scoring and mitigation logic: [service.py](/Users/aarya20067/Documents/Playground/src/breachwatch/service.py)

  }'- SHA-256 password matching helper: [security.py](/Users/aarya20067/Documents/Playground/src/breachwatch/security.py)

```- MongoDB and SQLite alert repositories: [repository.py](/Users/aarya20067/Documents/Playground/src/breachwatch/repository.py)



### Run historyRun a sample breach check:

```bash

curl http://localhost:8000/history?limit=10```bash

```cd /Users/aarya20067/Documents/Playground

PYTHONPATH=src .venv/bin/python3 -m breachwatch.cli check-email \

### Full API docs  --email alex.chen@example.com \

  --password winter2024!

When backend is running, visit: **http://localhost:8000/docs**```



(Interactive Swagger UI with all endpoints)Run the API:



---```bash

cd /Users/aarya20067/Documents/Playground

## DevelopmentPYTHONPATH=src .venv/bin/python3 -m breachwatch.cli serve-api --host 0.0.0.0 --port 8010

To run the UI against a remote breachwatch backend, set BINDTOX_API_URL to the backend URL before starting the Streamlit app.

### Run tests```



```bashMain breach endpoints:

export PYTHONPATH=src

python -m pytest tests/- `GET /health`

```- `POST /breach-check`

- `GET /dashboard`

### Project structure- `GET /alerts`



- **input_layer**: validates SMILES, ligand files, protein filesPersistence selection:

- **preprocessing**: prepares proteins and ligands for docking

- **docking**: runs AutoDock Vina, extracts binding energy- default SQLite mode: set nothing, alerts are stored in `artifacts/breachwatch_alerts.sqlite3`

- **binding_analysis**: interprets affinity and interaction patterns- MongoDB mode: set `BREACHWATCH_DB_MODE=mongo` and `BREACHWATCH_MONGO_URI=...`

- **toxicity**: trains and runs toxicity classifier- in-memory mode: set `BREACHWATCH_DB_MODE=memory`

- **orchestrator**: coordinates the full pipeline
- **backend_api**: FastAPI endpoints
- **streamlit_app**: web dashboard

---

## Notes

- **Binding site detection**: Uses co-crystallized ligand coordinates when present; falls back to geometric center
- **Receptor preparation**: If full prep fails, uses fallback PDBQT writer so docking can still proceed
- **Toxicity model**: Achieves ~77.8% accuracy on reference dataset
- **Portability**: All binaries (Vina) included; works on macOS (ARM64 + Intel), Linux, Windows
- **Network**: Backend and UI bind to `0.0.0.0` to allow cross-machine communication

---

## Citation

If you use BindTox in research, please cite this repository and the following tools:

- AutoDock Vina: [Trott & Olson (2010)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3041641/)
- RDKit: [Landrum et al.](https://www.rdkit.org/)
- Streamlit: [https://streamlit.io/](https://streamlit.io/)

---

## License

See `SETUP_GUIDE.md` for additional notes.

**BindTox** — computational chemistry toolkit for drug discovery screening.
