from __future__ import annotations

import json
from pathlib import Path

from .schemas import BreachRecord


DEFAULT_DATASET_PATH = Path("data/breachwatch/leaked_credentials.json")


def load_breach_dataset(dataset_path: Path | None = None) -> list[BreachRecord]:
    path = dataset_path or DEFAULT_DATASET_PATH
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [BreachRecord.model_validate(item) for item in payload]

