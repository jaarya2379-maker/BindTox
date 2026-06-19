from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DockingBoxSchema(BaseModel):
    center_x: float
    center_y: float
    center_z: float
    size_x: float = 20.0
    size_y: float = 20.0
    size_z: float = 20.0


class AnalysisRequestSchema(BaseModel):
    compound_name: str | None = None
    protein_name: str | None = None
    smiles: str | None = None
    receptor_path: str | None = None
    ligand_path: str | None = None
    model_path: str | None = "models/toxicity_model.joblib"
    workspace: str = "artifacts/api_run"
    database: str = "artifacts/bindtox.sqlite3"
    docking_box: DockingBoxSchema | None = None


class AnalysisResponseSchema(BaseModel):
    input_summary: dict[str, Any]
    preprocessing: dict[str, Any]
    descriptors: dict[str, Any]
    binding: dict[str, Any] | None
    docking: dict[str, Any] | None
    toxicity: dict[str, Any] | None
    run_id: int | None
