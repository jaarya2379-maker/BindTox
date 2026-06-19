from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Crippen, Descriptors, Lipinski, rdMolDescriptors
except ImportError:  # pragma: no cover - dependency is optional in the sandbox
    Chem = None
    AllChem = None
    Crippen = None
    Descriptors = None
    Lipinski = None
    rdMolDescriptors = None

from .utils import ensure_dir


class ChemistryDependencyError(RuntimeError):
    pass


@dataclass(slots=True)
class MolecularProperties:
    smiles: str
    molecular_weight: float
    logp: float
    h_bond_donors: int
    h_bond_acceptors: int
    tpsa: float
    rotatable_bonds: int
    heavy_atom_count: int
    lipinski_pass: bool
    lipinski_violations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require_rdkit() -> None:
    if Chem is None:
        raise ChemistryDependencyError(
            "RDKit is required for chemistry features. Install dependencies from requirements.txt."
        )


def smiles_to_mol(smiles: str):
    _require_rdkit()
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Unable to parse SMILES: {smiles}")
    return mol


def smiles_to_3d_mol(smiles: str):
    mol = smiles_to_mol(smiles)
    mol = Chem.AddHs(mol)
    status = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    if status != 0:
        raise ValueError(f"3D embedding failed for SMILES: {smiles}")
    AllChem.MMFFOptimizeMolecule(mol)
    return mol


def write_smiles_3d(smiles: str, output_path: Path) -> Path:
    mol = smiles_to_3d_mol(smiles)
    ensure_dir(output_path.parent)
    writer = Chem.SDWriter(str(output_path))
    writer.write(mol)
    writer.close()
    return output_path


def calculate_properties(smiles: str) -> MolecularProperties:
    mol = smiles_to_mol(smiles)
    violations: list[str] = []

    molecular_weight = round(Descriptors.MolWt(mol), 3)
    logp = round(Crippen.MolLogP(mol), 3)
    h_bond_donors = int(Lipinski.NumHDonors(mol))
    h_bond_acceptors = int(Lipinski.NumHAcceptors(mol))
    tpsa = round(rdMolDescriptors.CalcTPSA(mol), 3)
    rotatable_bonds = int(Lipinski.NumRotatableBonds(mol))
    heavy_atom_count = int(mol.GetNumHeavyAtoms())

    if molecular_weight > 500:
        violations.append("Molecular weight > 500")
    if logp > 5:
        violations.append("LogP > 5")
    if h_bond_donors > 5:
        violations.append("H-bond donors > 5")
    if h_bond_acceptors > 10:
        violations.append("H-bond acceptors > 10")

    return MolecularProperties(
        smiles=smiles,
        molecular_weight=molecular_weight,
        logp=logp,
        h_bond_donors=h_bond_donors,
        h_bond_acceptors=h_bond_acceptors,
        tpsa=tpsa,
        rotatable_bonds=rotatable_bonds,
        heavy_atom_count=heavy_atom_count,
        lipinski_pass=not violations,
        lipinski_violations=violations,
    )
