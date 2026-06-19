# BindTox

**Drug-protein docking and toxicity prediction toolkit for computational screening.**

BindTox combines molecular descriptor generation, AutoDock Vina-based docking, toxicity prediction, a FastAPI backend, and a Streamlit dashboard into one local-first workflow for early drug discovery experiments.

> BindTox is intended for research, education, prototyping, and demonstration workflows. It is not a substitute for validated clinical, regulatory, or laboratory decision-making.

## Highlights

- Molecular descriptor calculation from SMILES strings
- Ligand/protein docking workflows powered by AutoDock Vina
- ML-based toxicity classification with a bundled starter model
- End-to-end analysis pipeline with saved run history
- FastAPI backend for programmatic access
- Streamlit UI for interactive analysis and demos
- Docker Compose setup for backend + UI deployment
- LAN and ngrok helper scripts for quick sharing

## Repository Structure

```text
BindTox/
├── data/                  # Demo receptors, sample ligands, and toxicity reference data
├── models/                # Bundled starter toxicity model and metadata
├── src/
│   ├── bindtox/           # Core docking, chemistry, API, pipeline, and storage logic
│   └── breachwatch/       # Simulated breach-monitoring demo backend
├── tests/                 # Unit tests
├── tools/                 # Helper scripts and bundled Vina executable
├── streamlit_app.py       # Streamlit dashboard
├── pyproject.toml         # Python package metadata
├── docker-compose.yml     # Backend + UI services
└── Dockerfile
```

## Requirements

- Python 3.10+
- Conda or virtualenv
- RDKit
- AutoDock Vina-compatible binary, included at `tools/vina`
- Optional: Docker, Docker Compose, ngrok

For the smoothest local install, use conda because RDKit and chemistry dependencies are easier to install from conda-forge.

## Quick Start

```bash
git clone https://github.com/jaarya2379-maker/BindTox.git
cd BindTox

conda create -n bindtox python=3.10
conda activate bindtox
conda install -c conda-forge rdkit openbabel

python -m pip install -r requirements.txt
python -m pip install -e .
```

Start the backend API:

```bash
export PYTHONPATH=src
python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000
```

In a second terminal, start the UI:

```bash
./start_app.sh
```

Then open:

- UI: http://localhost:8501
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## CLI Usage

Calculate molecular descriptors:

```bash
PYTHONPATH=src python -m bindtox.cli descriptors --smiles "CCO"
```

Run docking against the bundled 1HSG receptor:

```bash
PYTHONPATH=src python -m bindtox.cli dock \
  --receptor data/receptors/1HSG.pdb \
  --ligand data/examples/1iep/1iep_ligand.sdf \
  --output-dir artifacts/docking_cli
```

Run an end-to-end analysis from SMILES:

```bash
PYTHONPATH=src python -m bindtox.cli analyze \
  --smiles "CCO" \
  --compound-name Ethanol \
  --receptor-pdb data/receptors/1HSG.pdb
```

Show recent saved runs:

```bash
PYTHONPATH=src python -m bindtox.cli history --limit 10
```

Train or refresh the toxicity model:

```bash
PYTHONPATH=src python -m bindtox.cli train-toxicity \
  --dataset data/toxicity_reference.csv \
  --output models/toxicity_model.joblib
```

## API

Run the FastAPI backend:

```bash
PYTHONPATH=src python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000
```

Primary endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health check |
| `GET` | `/history` | Recent saved analysis runs |
| `POST` | `/analyze` | JSON-based ligand/protein analysis |
| `POST` | `/upload-and-analyze` | File upload analysis workflow |

Interactive OpenAPI docs are available at `http://localhost:8000/docs` while the backend is running.

## Streamlit UI

The dashboard lives in `streamlit_app.py`. It can run against a local backend or a backend on another machine.

Local UI:

```bash
./start_app.sh
```

Point the UI at a specific backend:

```bash
BINDTOX_API_URL="http://192.168.1.10:8000" \
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

## Docker

Build and run the backend and UI:

```bash
docker compose up --build
```

Services:

- Backend API: http://localhost:8000
- Streamlit UI: http://localhost:8501

The `ui` service is configured to call the backend through the Compose network at `http://backend:8000`.

## Sharing

Run on a local network by binding the backend and UI to `0.0.0.0`, then open the UI from another device using the host machine's LAN IP.

For quick public demos with ngrok:

```bash
./tools/expose_with_ngrok.sh
```

Use proper authentication, HTTPS termination, and deployment hardening for any production or sensitive environment.

## Testing

Run the test suite:

```bash
PYTHONPATH=src python -m pytest -q
```

If `pytest` is not installed in your environment:

```bash
python -m pip install pytest
```

## Generated Files

BindTox writes run outputs under `artifacts/` by default. These outputs are intentionally ignored by git, along with Python caches, local virtual environments, SQLite databases, logs, and OS metadata.

## Notes

- `tools/vina` is included for local docking workflows.
- `data/breachwatch/leaked_credentials.json` contains simulated demo data only.
- `models/toxicity_model.joblib` is a starter model for local experimentation.
- See `GETTING_STARTED.md`, `SETUP_GUIDE.md`, `DEPLOYMENT_GUIDE.md`, and `QUICK_TEST.md` for additional workflows.

## License

No license file is currently included. Add a `LICENSE` file before distributing or reusing this project publicly under a defined open-source license.
