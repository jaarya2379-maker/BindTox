from __future__ import annotations

import argparse
import json
from pathlib import Path

from .chemistry import calculate_properties
from .input_layer import LigandInput, ProteinInput
from .docking import PocketBox, detect_binding_pocket, dock_from_inputs
from .orchestrator import run_drug_protein_simulation
from .pipeline import analyze_compound
from .storage import fetch_recent_runs, init_db
from .toxicity import train_toxicity_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bindtox",
        description="Drug-protein docking and toxicity prediction toolkit.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    descriptors_parser = subparsers.add_parser("descriptors", help="Calculate molecular descriptors.")
    descriptors_parser.add_argument("--smiles", required=True)

    train_parser = subparsers.add_parser("train-toxicity", help="Train toxicity classifier.")
    train_parser.add_argument("--dataset", default="data/toxicity_reference.csv")
    train_parser.add_argument("--output", default="models/toxicity_model.joblib")

    analyze_file_parser = subparsers.add_parser(
        "analyze-file",
        help="Run end-to-end analysis from ligand file and protein file inputs.",
    )
    analyze_file_parser.add_argument("--ligand", required=True)
    analyze_file_parser.add_argument("--compound-name")
    analyze_file_parser.add_argument("--protein-name")
    analyze_file_parser.add_argument("--receptor-pdb")
    analyze_file_parser.add_argument("--center-x", type=float)
    analyze_file_parser.add_argument("--center-y", type=float)
    analyze_file_parser.add_argument("--center-z", type=float)
    analyze_file_parser.add_argument("--size-x", type=float, default=22.0)
    analyze_file_parser.add_argument("--size-y", type=float, default=22.0)
    analyze_file_parser.add_argument("--size-z", type=float, default=22.0)
    analyze_file_parser.add_argument("--model-path", default="models/toxicity_model.joblib")
    analyze_file_parser.add_argument("--workspace", default="artifacts/file_run")
    analyze_file_parser.add_argument("--database", default="artifacts/bindtox.sqlite3")

    dock_parser = subparsers.add_parser("dock", help="Run docking and return binding energy.")
    dock_parser.add_argument("--receptor", required=True, help="Path to receptor PDB or PDBQT.")
    dock_parser.add_argument("--ligand", required=True, help="Path to ligand SDF, MOL2, or PDBQT.")
    dock_parser.add_argument("--output-dir", default="artifacts/docking_cli")
    dock_parser.add_argument("--center-x", type=float)
    dock_parser.add_argument("--center-y", type=float)
    dock_parser.add_argument("--center-z", type=float)
    dock_parser.add_argument("--size-x", type=float, default=22.0)
    dock_parser.add_argument("--size-y", type=float, default=22.0)
    dock_parser.add_argument("--size-z", type=float, default=22.0)
    dock_parser.add_argument("--exhaustiveness", type=int, default=8)
    dock_parser.add_argument("--num-modes", type=int, default=9)

    analyze_parser = subparsers.add_parser("analyze", help="Run end-to-end analysis.")
    analyze_parser.add_argument("--smiles", required=True)
    analyze_parser.add_argument("--compound-name")
    analyze_parser.add_argument("--protein-name")
    analyze_parser.add_argument("--receptor-pdb")
    analyze_parser.add_argument("--center-x", type=float)
    analyze_parser.add_argument("--center-y", type=float)
    analyze_parser.add_argument("--center-z", type=float)
    analyze_parser.add_argument("--size-x", type=float, default=22.0)
    analyze_parser.add_argument("--size-y", type=float, default=22.0)
    analyze_parser.add_argument("--size-z", type=float, default=22.0)
    analyze_parser.add_argument("--model-path", default="models/toxicity_model.joblib")
    analyze_parser.add_argument("--workspace", default="artifacts/latest_run")
    analyze_parser.add_argument("--database", default="artifacts/bindtox.sqlite3")

    history_parser = subparsers.add_parser("history", help="Show recent saved runs.")
    history_parser.add_argument("--database", default="artifacts/bindtox.sqlite3")
    history_parser.add_argument("--limit", type=int, default=10)

    api_parser = subparsers.add_parser("serve-api", help="Run the FastAPI backend.")
    api_parser.add_argument("--host", default="0.0.0.0")
    api_parser.add_argument("--port", type=int, default=8000)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "descriptors":
        print(json.dumps(calculate_properties(args.smiles).to_dict(), indent=2))
        return

    if args.command == "train-toxicity":
        result = train_toxicity_model(Path(args.dataset), Path(args.output))
        print(json.dumps(result.to_dict(), indent=2))
        return

    if args.command == "analyze-file":
        analyze_pocket = None
        if args.center_x is not None and args.center_y is not None and args.center_z is not None:
            analyze_pocket = PocketBox(
                center_x=args.center_x,
                center_y=args.center_y,
                center_z=args.center_z,
                size_x=args.size_x,
                size_y=args.size_y,
                size_z=args.size_z,
            )
        result = run_drug_protein_simulation(
            compound_name=args.compound_name,
            protein_name=args.protein_name,
            ligand_input=LigandInput(file_path=Path(args.ligand)),
            protein_input=ProteinInput(file_path=Path(args.receptor_pdb)) if args.receptor_pdb else None,
            model_path=Path(args.model_path) if args.model_path else None,
            workspace=Path(args.workspace),
            db_path=Path(args.database) if args.database else None,
            pocket=analyze_pocket,
        )
        print(json.dumps(result.to_dict(), indent=2))
        return

    if args.command == "dock":
        receptor_path = Path(args.receptor)
        if args.center_x is not None and args.center_y is not None and args.center_z is not None:
            pocket = PocketBox(
                center_x=args.center_x,
                center_y=args.center_y,
                center_z=args.center_z,
                size_x=args.size_x,
                size_y=args.size_y,
                size_z=args.size_z,
            )
        else:
            if receptor_path.suffix.lower() == ".pdbqt":
                parser.error("Automatic pocket detection requires a receptor PDB file. Supply --center-* with PDBQT.")
            pocket = detect_binding_pocket(receptor_path)
            pocket.size_x = args.size_x
            pocket.size_y = args.size_y
            pocket.size_z = args.size_z

        result = dock_from_inputs(
            receptor_input=receptor_path,
            ligand_input=Path(args.ligand),
            output_dir=Path(args.output_dir),
            pocket=pocket,
            exhaustiveness=args.exhaustiveness,
            num_modes=args.num_modes,
        )
        print(json.dumps(result.to_dict(), indent=2))
        return

    if args.command == "analyze":
        analyze_pocket = None
        if args.center_x is not None and args.center_y is not None and args.center_z is not None:
            analyze_pocket = PocketBox(
                center_x=args.center_x,
                center_y=args.center_y,
                center_z=args.center_z,
                size_x=args.size_x,
                size_y=args.size_y,
                size_z=args.size_z,
            )
        result = analyze_compound(
            smiles=args.smiles,
            compound_name=args.compound_name,
            protein_name=args.protein_name,
            receptor_pdb=Path(args.receptor_pdb) if args.receptor_pdb else None,
            model_path=Path(args.model_path) if args.model_path else None,
            workspace=Path(args.workspace),
            db_path=Path(args.database) if args.database else None,
            pocket=analyze_pocket,
        )
        print(json.dumps(result.to_dict(), indent=2))
        return

    if args.command == "history":
        db_path = init_db(Path(args.database))
        print(json.dumps(fetch_recent_runs(db_path, limit=args.limit), indent=2))
        return

    if args.command == "serve-api":
        import uvicorn

        uvicorn.run("bindtox.backend_api:app", host=args.host, port=args.port, reload=False)
        return


if __name__ == "__main__":
    main()
