from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .binding_analysis import summarize_binding
from .chemistry import calculate_properties
from .docking import PocketBox, run_vina
from .input_layer import LigandInput, ProteinInput
from .preprocessing import (
    PreprocessingResult,
    preprocess_ligand_from_file,
    preprocess_ligand_from_smiles,
    preprocess_protein,
)
from .storage import init_db, save_run
from .toxicity import predict_toxicity
from .utils import ensure_dir, write_json


@dataclass(slots=True)
class SimulatorResult:
    input_summary: dict[str, Any]
    preprocessing: dict[str, Any]
    descriptors: dict[str, Any]
    binding: dict[str, Any] | None
    docking: dict[str, Any] | None
    toxicity: dict[str, Any] | None
    run_id: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_drug_protein_simulation(
    *,
    compound_name: str | None,
    protein_name: str | None,
    ligand_input: LigandInput,
    protein_input: ProteinInput | None,
    model_path: Path | None,
    workspace: Path,
    db_path: Path | None,
    pocket: PocketBox | None = None,
) -> SimulatorResult:
    workspace = ensure_dir(workspace.resolve())
    prep_dir = ensure_dir(workspace / "preprocessing")

    descriptors_source = ligand_input.smiles
    ligand_sdf_path: Path | None = None
    if ligand_input.file_path is not None:
        ligand_prepared_path = preprocess_ligand_from_file(ligand_input.file_path, prep_dir)
        if ligand_input.smiles is None:
            descriptors_source = compound_name or ligand_input.file_path.stem
    else:
        if ligand_input.smiles is None:
            raise ValueError("A ligand SMILES or ligand file is required.")
        ligand_sdf_path, ligand_prepared_path = preprocess_ligand_from_smiles(ligand_input.smiles, prep_dir)

    if ligand_input.smiles is None:
        raise ValueError("SMILES input is required for descriptor and toxicity analysis.")

    descriptors = calculate_properties(ligand_input.smiles).to_dict()

    docking_payload = None
    preprocessing_payload = PreprocessingResult(
        receptor_input_path=str(protein_input.file_path) if protein_input else None,
        receptor_prepared_path=None,
        ligand_input_path=str(ligand_input.file_path) if ligand_input.file_path else None,
        ligand_prepared_path=str(ligand_prepared_path),
        ligand_sdf_path=str(ligand_sdf_path) if ligand_sdf_path else None,
        pocket=None,
    )

    if protein_input is not None:
        receptor_prepared_path, active_pocket = preprocess_protein(
            protein_input.file_path,
            prep_dir,
            pocket=pocket,
        )
        preprocessing_payload.receptor_prepared_path = str(receptor_prepared_path)
        preprocessing_payload.pocket = asdict(active_pocket)
        docking_payload = run_vina(
            receptor_pdbqt=receptor_prepared_path,
            ligand_pdbqt=ligand_prepared_path,
            pocket=active_pocket,
            output_dir=workspace / "docking",
        ).to_dict()

    toxicity_payload = None
    if model_path is not None and model_path.exists():
        toxicity_payload = predict_toxicity(ligand_input.smiles, model_path)

    binding_payload = summarize_binding(
        docking_payload["binding_energy"] if docking_payload else None,
        descriptors,
    )

    run_id = None
    if db_path is not None:
        init_db(db_path)
        run_id = save_run(
            db_path,
            drug_name=compound_name,
            smiles=ligand_input.smiles,
            protein_name=protein_name,
            receptor_path=str(protein_input.file_path.resolve()) if protein_input else None,
            descriptors=descriptors,
            binding_energy=docking_payload["binding_energy"] if docking_payload else None,
            toxicity_label=toxicity_payload["label"] if toxicity_payload else None,
            toxicity_probability=toxicity_payload["probability"] if toxicity_payload else None,
            docking_result=docking_payload,
        )

    result = SimulatorResult(
        input_summary={
            "compound_name": compound_name,
            "protein_name": protein_name,
            "ligand": ligand_input.to_dict(),
            "protein": protein_input.to_dict() if protein_input else None,
        },
        preprocessing=preprocessing_payload.to_dict(),
        descriptors=descriptors,
        binding=binding_payload.to_dict() if binding_payload else None,
        docking=docking_payload,
        toxicity=toxicity_payload,
        run_id=run_id,
    )
    write_json(workspace / "analysis_result.json", result.to_dict())
    return result
