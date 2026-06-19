from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .utils import ensure_dir


SUPPORTED_LIGAND_SUFFIXES = {".sdf", ".mol", ".mol2", ".pdbqt"}
SUPPORTED_PROTEIN_SUFFIXES = {".pdb", ".pdbqt"}


@dataclass(slots=True)
class LigandInput:
    smiles: str | None = None
    file_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["file_path"] = str(self.file_path) if self.file_path else None
        return payload


@dataclass(slots=True)
class ProteinInput:
    file_path: Path

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["file_path"] = str(self.file_path)
        return payload


def validate_smiles(smiles: str) -> str:
    cleaned = smiles.strip()
    if not cleaned:
        raise ValueError("SMILES input is required.")
    return cleaned


def validate_ligand_file(file_path: Path) -> Path:
    if not file_path.exists():
        raise FileNotFoundError(f"Ligand file not found: {file_path}")
    if file_path.suffix.lower() not in SUPPORTED_LIGAND_SUFFIXES:
        raise ValueError(f"Unsupported ligand format: {file_path.suffix}")
    return file_path.resolve()


def validate_protein_file(file_path: Path) -> Path:
    if not file_path.exists():
        raise FileNotFoundError(f"Protein file not found: {file_path}")
    if file_path.suffix.lower() not in SUPPORTED_PROTEIN_SUFFIXES:
        raise ValueError(f"Unsupported protein format: {file_path.suffix}")
    return file_path.resolve()


def save_uploaded_file(filename: str, content: bytes, target_dir: Path) -> Path:
    ensure_dir(target_dir)
    safe_name = Path(filename).name
    output_path = target_dir / safe_name
    output_path.write_bytes(content)
    return output_path
