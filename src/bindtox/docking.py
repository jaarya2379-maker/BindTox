from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .utils import ensure_dir, write_json


class DockingDependencyError(RuntimeError):
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WATER_RESIDUES = {"HOH", "WAT", "H2O"}


@dataclass(slots=True)
class PocketBox:
    center_x: float
    center_y: float
    center_z: float
    size_x: float = 22.0
    size_y: float = 22.0
    size_z: float = 22.0


@dataclass(slots=True)
class DockingResult:
    binding_energy: float
    pose_rank: int
    receptor_path: str
    ligand_path: str
    output_pose_path: str
    log_path: str
    pocket: PocketBox
    raw_scores: list[dict[str, float]]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["pocket"] = asdict(self.pocket)
        return payload


def _require_binary(name: str) -> str:
    import os
    import sys
    
    candidates = [
        PROJECT_ROOT / "tools" / name,
        PROJECT_ROOT / ".venv" / "bin" / name,
        Path(sys.prefix) / "bin" / name,  # Current Python environment
    ]
    
    # Add conda environment paths if available
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        candidates.append(Path(conda_prefix) / "bin" / name)
    
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    path = shutil.which(name)
    if not path:
        raise DockingDependencyError(f"Required binary not found in PATH: {name}")
    return path


def preprocess_receptor(receptor_pdb: Path, receptor_pdbqt: Path) -> Path:
    receptor_pdb = receptor_pdb.resolve()
    receptor_pdbqt = receptor_pdbqt.resolve()
    ensure_dir(receptor_pdbqt.parent)
    cleaned_pdb = _clean_receptor_pdb(receptor_pdb, receptor_pdbqt.with_suffix(".cleaned.pdb"))

    mk_receptor = _optional_binary("mk_prepare_receptor.py")
    prepare_receptor = _optional_binary("prepare_receptor")
    if mk_receptor:
        cmd = [mk_receptor, "--read_pdb", str(cleaned_pdb), "-o", str(receptor_pdbqt.with_suffix("")), "-p"]
    elif prepare_receptor:
        cmd = [prepare_receptor, "-r", str(cleaned_pdb), "-o", str(receptor_pdbqt)]
    else:
        raise DockingDependencyError(
            "No receptor preparation binary found. Install AutoDockTools or Meeko."
        )

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        _write_basic_receptor_pdbqt(cleaned_pdb, receptor_pdbqt)
    return receptor_pdbqt


def preprocess_ligand(ligand_input: Path, ligand_pdbqt: Path) -> Path:
    ligand_input = ligand_input.resolve()
    ligand_pdbqt = ligand_pdbqt.resolve()
    ensure_dir(ligand_pdbqt.parent)

    mk_ligand = _optional_binary("mk_prepare_ligand.py")
    prepare_ligand = _optional_binary("prepare_ligand")
    obabel = _optional_binary("obabel")

    if mk_ligand:
        cmd = [mk_ligand, "-i", str(ligand_input), "-o", str(ligand_pdbqt)]
    elif prepare_ligand:
        cmd = [prepare_ligand, "-l", str(ligand_input), "-o", str(ligand_pdbqt)]
    elif obabel:
        cmd = [obabel, str(ligand_input), "-O", str(ligand_pdbqt)]
    else:
        raise DockingDependencyError(
            "No ligand preparation binary found. Install Meeko, AutoDockTools, or Open Babel."
        )

    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return ligand_pdbqt


def _optional_binary(name: str) -> str | None:
    try:
        return _require_binary(name)
    except DockingDependencyError:
        return None


def detect_binding_pocket(receptor_pdb: Path) -> PocketBox:
    ligand_coords: list[tuple[float, float, float]] = []
    protein_coords: list[tuple[float, float, float]] = []
    for line in receptor_pdb.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            x = float(line[30:38].strip())
            y = float(line[38:46].strip())
            z = float(line[46:54].strip())
        except ValueError:
            continue

        residue = line[17:20].strip()
        if line.startswith("HETATM") and residue not in WATER_RESIDUES:
            ligand_coords.append((x, y, z))
        elif line.startswith("ATOM"):
            protein_coords.append((x, y, z))

    coords = ligand_coords or protein_coords
    if not coords:
        raise ValueError(f"No atom coordinates found in receptor file: {receptor_pdb}")

    center_x = round(sum(x for x, _, _ in coords) / len(coords), 3)
    center_y = round(sum(y for _, y, _ in coords) / len(coords), 3)
    center_z = round(sum(z for _, _, z in coords) / len(coords), 3)
    return PocketBox(center_x=center_x, center_y=center_y, center_z=center_z)


def _clean_receptor_pdb(receptor_pdb: Path, output_path: Path) -> Path:
    cleaned_lines: list[str] = []
    for line in receptor_pdb.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("ATOM"):
            atom_name = line[12:16].strip()
            element = line[76:78].strip()
            if element == "H" or atom_name.startswith("H"):
                continue
            cleaned_lines.append(line)
            continue
        if line.startswith("TER"):
            cleaned_lines.append(line)
            continue
        if line.startswith("END"):
            cleaned_lines.append(line)

    if not cleaned_lines:
        raise ValueError(f"Failed to extract protein atoms from receptor file: {receptor_pdb}")

    output_path.write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")
    return output_path


def _write_basic_receptor_pdbqt(cleaned_pdb: Path, receptor_pdbqt: Path) -> Path:
    lines: list[str] = []
    serial = 1
    for line in cleaned_pdb.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("ATOM"):
            continue
        atom_name = line[12:16]
        residue_name = line[17:20]
        chain_id = line[21:22]
        residue_seq = line[22:26]
        x = line[30:38]
        y = line[38:46]
        z = line[46:54]
        occupancy = line[54:60]
        temp_factor = line[60:66]
        element = line[76:78].strip() or atom_name.strip()[0]
        atom_type = _basic_autodock_type(atom_name.strip(), element)
        pdbqt_line = (
            f"ATOM  {serial:5d} {atom_name:<4}{residue_name:>4} {chain_id}{residue_seq:>4}    "
            f"{x}{y}{z}{occupancy}{temp_factor}    {0.000:>6.3f} {atom_type:<2}"
        )
        lines.append(pdbqt_line)
        serial += 1

    if not lines:
        raise ValueError(f"Failed to create fallback receptor PDBQT from {cleaned_pdb}")

    receptor_pdbqt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return receptor_pdbqt


def _basic_autodock_type(atom_name: str, element: str) -> str:
    upper_element = element.upper()
    if upper_element == "O":
        return "OA"
    if upper_element == "N":
        return "N"
    if upper_element == "S":
        return "SA"
    if upper_element == "P":
        return "P"
    if upper_element == "H":
        return "HD"
    if upper_element == "C":
        return "A" if atom_name.startswith(("CG", "CD", "CE", "CZ", "CH")) else "C"
    return upper_element[:2]


def extract_scores(log_path: Path) -> list[dict[str, float]]:
    scores: list[dict[str, float]] = []
    number = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
    pattern = re.compile(rf"^\s*(\d+)\s+({number})\s+({number})\s+({number})")
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.match(line)
        if match:
            scores.append(
                {
                    "mode": int(match.group(1)),
                    "energy": float(match.group(2)),
                    "rmsd_lb": float(match.group(3)),
                    "rmsd_ub": float(match.group(4)),
                }
            )
    if not scores:
        raise ValueError(f"No Vina scores found in {log_path}")
    return scores


def run_vina(
    receptor_pdbqt: Path,
    ligand_pdbqt: Path,
    pocket: PocketBox,
    output_dir: Path,
    exhaustiveness: int = 8,
    num_modes: int = 9,
) -> DockingResult:
    vina = _require_binary("vina")
    output_dir = ensure_dir(output_dir.resolve())
    out_pose = output_dir / "docked_pose.pdbqt"
    log_path = output_dir / "vina.log"

    cmd = [
        vina,
        "--receptor",
        str(receptor_pdbqt.resolve()),
        "--ligand",
        str(ligand_pdbqt.resolve()),
        "--center_x",
        str(pocket.center_x),
        "--center_y",
        str(pocket.center_y),
        "--center_z",
        str(pocket.center_z),
        "--size_x",
        str(pocket.size_x),
        "--size_y",
        str(pocket.size_y),
        "--size_z",
        str(pocket.size_z),
        "--out",
        str(out_pose),
        "--exhaustiveness",
        str(exhaustiveness),
        "--num_modes",
        str(num_modes),
    ]

    try:
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        combined_output = "\n".join(part for part in (exc.stdout, exc.stderr) if part)
        if combined_output:
            log_path.write_text(combined_output, encoding="utf-8")
        raise RuntimeError(f"AutoDock Vina failed. See log: {log_path}") from exc

    combined_output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    log_path.write_text(combined_output, encoding="utf-8")
    scores = extract_scores(log_path)
    best_score = scores[0]
    result = DockingResult(
        binding_energy=best_score["energy"],
        pose_rank=int(best_score["mode"]),
        receptor_path=str(receptor_pdbqt.resolve()),
        ligand_path=str(ligand_pdbqt.resolve()),
        output_pose_path=str(out_pose),
        log_path=str(log_path),
        pocket=pocket,
        raw_scores=scores,
    )
    write_json(output_dir / "docking_result.json", result.to_dict())
    return result


def dock_from_inputs(
    *,
    receptor_input: Path,
    ligand_input: Path,
    output_dir: Path,
    pocket: PocketBox,
    exhaustiveness: int = 8,
    num_modes: int = 9,
) -> DockingResult:
    output_dir = ensure_dir(output_dir.resolve())

    if receptor_input.suffix.lower() == ".pdbqt":
        receptor_pdbqt = receptor_input.resolve()
    else:
        receptor_pdbqt = preprocess_receptor(receptor_input, output_dir / "receptor.pdbqt")

    if ligand_input.suffix.lower() == ".pdbqt":
        ligand_pdbqt = ligand_input.resolve()
    else:
        ligand_pdbqt = preprocess_ligand(ligand_input, output_dir / "ligand.pdbqt")

    return run_vina(
        receptor_pdbqt=receptor_pdbqt,
        ligand_pdbqt=ligand_pdbqt,
        pocket=pocket,
        output_dir=output_dir,
        exhaustiveness=exhaustiveness,
        num_modes=num_modes,
    )
