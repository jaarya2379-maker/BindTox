from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .docking import PocketBox
from .input_layer import LigandInput, ProteinInput
from .orchestrator import run_drug_protein_simulation


@dataclass(slots=True)
class AnalysisResult:
    input_summary: dict[str, Any]
    preprocessing: dict[str, Any]
    descriptors: dict[str, Any]
    binding: dict[str, Any] | None
    docking: dict[str, Any] | None
    toxicity: dict[str, Any] | None
    run_id: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_compound(
    *,
    smiles: str,
    compound_name: str | None,
    protein_name: str | None,
    receptor_pdb: Path | None,
    model_path: Path | None,
    workspace: Path,
    db_path: Path | None,
    pocket: PocketBox | None = None,
) -> AnalysisResult:
    result = run_drug_protein_simulation(
        compound_name=compound_name,
        protein_name=protein_name,
        ligand_input=LigandInput(smiles=smiles),
        protein_input=ProteinInput(file_path=receptor_pdb) if receptor_pdb else None,
        model_path=model_path,
        workspace=workspace,
        db_path=db_path,
        pocket=pocket,
    )
    return AnalysisResult(**result.to_dict())
