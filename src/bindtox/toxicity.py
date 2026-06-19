from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import train_test_split
except ImportError:  # pragma: no cover
    joblib = None
    pd = None
    RandomForestClassifier = None
    accuracy_score = None
    classification_report = None
    train_test_split = None

from .chemistry import calculate_properties
from .utils import ensure_dir, write_json


class ToxicityDependencyError(RuntimeError):
    pass


FEATURE_COLUMNS = [
    "molecular_weight",
    "logp",
    "h_bond_donors",
    "h_bond_acceptors",
    "tpsa",
    "rotatable_bonds",
    "heavy_atom_count",
]


@dataclass(slots=True)
class TrainingResult:
    accuracy: float
    train_size: int
    test_size: int
    model_path: str
    report: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require_ml_stack() -> None:
    if any(
        dependency is None
        for dependency in (
            joblib,
            pd,
            RandomForestClassifier,
            accuracy_score,
            classification_report,
            train_test_split,
        )
    ):
        raise ToxicityDependencyError(
            "pandas, scikit-learn, and joblib are required for toxicity model training."
        )


def build_feature_frame(dataset_path: Path):
    _require_ml_stack()
    source = pd.read_csv(dataset_path)
    records = []
    for row in source.to_dict(orient="records"):
        properties = calculate_properties(row["smiles"]).to_dict()
        records.append(
            {
                "compound": row["compound"],
                "smiles": row["smiles"],
                "label": row["label"],
                **{key: properties[key] for key in FEATURE_COLUMNS},
            }
        )
    return pd.DataFrame(records)


def train_toxicity_model(
    dataset_path: Path,
    model_path: Path,
    random_state: int = 42,
) -> TrainingResult:
    frame = build_feature_frame(dataset_path)
    X = frame[FEATURE_COLUMNS]
    y = frame["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=random_state,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=1,
        random_state=random_state,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = float(accuracy_score(y_test, predictions))
    report = classification_report(y_test, predictions)

    ensure_dir(model_path.parent)
    joblib.dump({"model": model, "features": FEATURE_COLUMNS}, model_path)
    metadata_path = model_path.with_suffix(".metadata.json")
    write_json(
        metadata_path,
        {
            "accuracy": accuracy,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "features": FEATURE_COLUMNS,
            "report": report,
            "model_path": str(model_path.resolve()),
        },
    )
    return TrainingResult(
        accuracy=accuracy,
        train_size=len(X_train),
        test_size=len(X_test),
        model_path=str(model_path.resolve()),
        report=report,
    )


def load_model(model_path: Path):
    _require_ml_stack()
    return joblib.load(model_path)


def predict_toxicity(smiles: str, model_path: Path) -> dict[str, Any]:
    bundle = load_model(model_path)
    properties = calculate_properties(smiles).to_dict()
    frame = pd.DataFrame([{key: properties[key] for key in bundle["features"]}])
    probabilities = bundle["model"].predict_proba(frame)[0]
    classes = list(bundle["model"].classes_)
    best_idx = int(probabilities.argmax())
    return {
        "label": str(classes[best_idx]),
        "probability": float(probabilities[best_idx]),
        "class_probabilities": {
            str(label): float(prob) for label, prob in zip(classes, probabilities, strict=False)
        },
    }
