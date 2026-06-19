from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .chemistry import write_smiles_3d
from .docking import PocketBox, detect_binding_pocket, preprocess_ligand, preprocess_receptor
from .input_layer import validate_ligand_file, validate_protein_file, validate_smiles
from .utils import ensure_dir


@dataclass(slots=True)
class PreprocessingResult:
    receptor_input_path: str | None
    receptor_prepared_path: str | None
    ligand_input_path: str | None
    ligand_prepared_path: str
    ligand_sdf_path: str | None
    pocket: dict[str, float] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def preprocess_protein(
    protein_path: Path,
    output_dir: Path,
    pocket: PocketBox | None = None,
) -> tuple[Path, PocketBox]:
    protein_path = validate_protein_file(protein_path)
    output_dir = ensure_dir(output_dir)

    if protein_path.suffix.lower() == ".pdbqt":
        prepared_path = protein_path
        active_pocket = pocket
        if active_pocket is None:
            raise ValueError("Protein PDBQT inputs require an explicit docking box.")
    else:
        active_pocket = pocket or detect_binding_pocket(protein_path)
        prepared_path = preprocess_receptor(protein_path, output_dir / "receptor.pdbqt")

    return prepared_path, active_pocket


def preprocess_ligand_from_smiles(smiles: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir = ensure_dir(output_dir)
    smiles = validate_smiles(smiles)
    ligand_sdf = write_smiles_3d(smiles, output_dir / "ligand.sdf")
    ligand_pdbqt = preprocess_ligand(ligand_sdf, output_dir / "ligand.pdbqt")
    return ligand_sdf, ligand_pdbqt


def preprocess_ligand_from_file(file_path: Path, output_dir: Path) -> Path:
    output_dir = ensure_dir(output_dir)
    file_path = validate_ligand_file(file_path)
    if file_path.suffix.lower() == ".pdbqt":
        return file_path
    return preprocess_ligand(file_path, output_dir / "ligand.pdbqt")
