from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_name TEXT,
    smiles TEXT NOT NULL,
    protein_name TEXT,
    receptor_path TEXT,
    binding_energy REAL,
    toxicity_label TEXT,
    toxicity_probability REAL,
    descriptors_json TEXT NOT NULL,
    docking_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(db_path: Path) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
    return db_path


def save_run(
    db_path: Path,
    *,
    drug_name: str | None,
    smiles: str,
    protein_name: str | None,
    receptor_path: str | None,
    descriptors: dict[str, Any],
    binding_energy: float | None,
    toxicity_label: str | None,
    toxicity_probability: float | None,
    docking_result: dict[str, Any] | None,
) -> int:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO analysis_runs (
                drug_name, smiles, protein_name, receptor_path, binding_energy,
                toxicity_label, toxicity_probability, descriptors_json, docking_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                drug_name,
                smiles,
                protein_name,
                receptor_path,
                binding_energy,
                toxicity_label,
                toxicity_probability,
                json.dumps(descriptors),
                json.dumps(docking_result) if docking_result else None,
            ),
        )
        return int(cursor.lastrowid)


def fetch_recent_runs(db_path: Path, limit: int = 25) -> list[dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM analysis_runs ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
