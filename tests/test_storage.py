from pathlib import Path

from bindtox.storage import fetch_recent_runs, init_db, save_run


def test_storage_round_trip(tmp_path: Path):
    db_path = init_db(tmp_path / "bindtox.sqlite3")
    run_id = save_run(
        db_path,
        drug_name="Aspirin",
        smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
        protein_name="COX2",
        receptor_path="/tmp/receptor.pdb",
        descriptors={"molecular_weight": 180.159},
        binding_energy=-7.4,
        toxicity_label="Non-toxic",
        toxicity_probability=0.82,
        docking_result={"binding_energy": -7.4},
    )
    rows = fetch_recent_runs(db_path, limit=5)
    assert run_id == 1
    assert len(rows) == 1
    assert rows[0]["drug_name"] == "Aspirin"
