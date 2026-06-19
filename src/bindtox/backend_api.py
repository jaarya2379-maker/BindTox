from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

from .docking import PocketBox
from .input_layer import LigandInput, ProteinInput, save_uploaded_file
from .orchestrator import run_drug_protein_simulation
from .schemas import AnalysisRequestSchema
from .storage import fetch_recent_runs, init_db


app = FastAPI(title="BindTox Backend API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/history")
def history(database: str = "artifacts/bindtox.sqlite3", limit: int = 10):
    db_path = init_db(Path(database))
    return fetch_recent_runs(db_path, limit=limit)


@app.post("/analyze")
def analyze(request: AnalysisRequestSchema):
    pocket = None
    if request.docking_box is not None:
        pocket = PocketBox(**request.docking_box.model_dump())

    result = run_drug_protein_simulation(
        compound_name=request.compound_name,
        protein_name=request.protein_name,
        ligand_input=LigandInput(
            smiles=request.smiles,
            file_path=Path(request.ligand_path) if request.ligand_path else None,
        ),
        protein_input=ProteinInput(file_path=Path(request.receptor_path)) if request.receptor_path else None,
        model_path=Path(request.model_path) if request.model_path else None,
        workspace=Path(request.workspace),
        db_path=Path(request.database) if request.database else None,
        pocket=pocket,
    )
    return JSONResponse(result.to_dict())


@app.post("/upload-and-analyze")
async def upload_and_analyze(
    compound_name: str | None = Form(default=None),
    protein_name: str | None = Form(default=None),
    smiles: str | None = Form(default=None),
    model_path: str = Form(default="models/toxicity_model.joblib"),
    workspace: str = Form(default="artifacts/api_upload_run"),
    database: str = Form(default="artifacts/bindtox.sqlite3"),
    receptor_file: UploadFile | None = File(default=None),
    ligand_file: UploadFile | None = File(default=None),
):
    upload_dir = Path(workspace) / "uploads"
    receptor_path = None
    ligand_path = None

    if receptor_file is not None:
        receptor_path = save_uploaded_file(receptor_file.filename, await receptor_file.read(), upload_dir)
    if ligand_file is not None:
        ligand_path = save_uploaded_file(ligand_file.filename, await ligand_file.read(), upload_dir)

    result = run_drug_protein_simulation(
        compound_name=compound_name,
        protein_name=protein_name,
        ligand_input=LigandInput(smiles=smiles, file_path=ligand_path),
        protein_input=ProteinInput(file_path=receptor_path) if receptor_path else None,
        model_path=Path(model_path),
        workspace=Path(workspace),
        db_path=Path(database),
    )
    return JSONResponse(result.to_dict())
