from __future__ import annotations

import json
import shutil
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

from bindtox.chemistry import calculate_properties, write_smiles_3d, ChemistryDependencyError
from bindtox.binding_analysis import summarize_binding
from bindtox.docking import PocketBox, detect_binding_pocket
from bindtox.toxicity import train_toxicity_model
from bindtox.utils import ensure_dir, read_json

try:
    import py3Dmol
except ImportError:  # pragma: no cover
    py3Dmol = None


st.set_page_config(page_title="Drug-Protein Binding Platform", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_RECEPTOR_PATH = PROJECT_ROOT / "artifacts" / "uploads" / "1HSG.pdb"


def receptor_candidates(filename: str) -> list[Path]:
    return [
        PROJECT_ROOT / "artifacts" / "uploads" / filename,
        PROJECT_ROOT / "artifacts" / "dashboard_run" / "uploads" / filename,
        PROJECT_ROOT / "artifacts" / "api_contract_test" / "uploads" / filename,
        PROJECT_ROOT / "data" / "receptors" / filename,
    ]


def first_existing_path(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


RECEPTOR_PRESETS = {
    "1HSG": {
        "filename": "1HSG.pdb",
        "protein_name": "Hemoglobin",
        "compound_presets": {
            "Aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
            "Ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
            "Caffeine": "CN1C(=O)N(C)c2ncn(C)c2C1=O",
            "Warfarin": "CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O",
        },
    },
    "4HHB": {
        "filename": "4HHB.pdb",
        "protein_name": "Hemoglobin",
        "compound_presets": {
            "Paracetamol": "CC(=O)NC1=CC=C(O)C=C1O",
            "Nicotine": "CN1CCC[C@H]1c2cccnc2",
            "Caffeine": "CN1C(=O)N(C)c2ncn(C)c2C1=O",
            "Ethanol": "CCO",
        },
    },
}
UPLOAD_DIR = Path("artifacts/uploads")
db_path = Path("artifacts/bindtox.sqlite3")
MODEL_PATH_DEFAULT = Path("models/toxicity_model.joblib")
DATASET_PATH_DEFAULT = Path("data/toxicity_reference.csv")
import os

# Allow overriding the API base URL via env var so the UI can point to a backend on another host
API_BASE_URL_DEFAULT = os.environ.get("BINDTOX_API_URL", "http://0.0.0.0:8000")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f5fffd;
            --panel: #d8f4ef;
            --card: #ffffff;
            --card-soft: #eefcf8;
            --line: #b7dfd8;
            --text: #153d38;
            --muted: #5d8d86;
            --green: #d8f4e7;
            --green-ink: #1e7e63;
            --blue: #dff2ff;
            --blue-ink: #2b73b6;
            --danger: #d25555;
            --sea: #20b2aa;
        }
        .stApp {
            background: var(--bg);
            color: var(--text);
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(32, 178, 170, 0.14), transparent 24%),
                radial-gradient(circle at top right, rgba(178, 240, 233, 0.35), transparent 28%),
                linear-gradient(180deg, #f9fffe 0%, #f1fcf9 45%, #f5fffd 100%);
        }
        [data-testid="stHeader"] {
            background: rgba(245, 255, 253, 0.92);
        }
        [data-testid="stSidebar"] {
            background: var(--panel);
            border-right: 1px solid rgba(21, 61, 56, 0.07);
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1.25rem;
        }
        .block-container {
            max-width: 1220px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3, h4, p, label, span, div {
            color: var(--text);
        }
        .hero-title {
            font-size: 2.45rem;
            line-height: 1.05;
            letter-spacing: -0.04em;
            margin: 0 0 1.25rem;
            font-weight: 800;
            color: #12453f;
        }
        .section-divider {
            border-top: 1px solid #d0ece6;
            margin: 0.5rem 0 2rem;
        }
        .section-title {
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 0.9rem;
            color: #1c5750;
        }
        .card-shell {
            background: transparent;
            border-radius: 22px;
            padding: 0.2rem 0;
        }
        .status-banner {
            padding: 1rem 1.1rem;
            border-radius: 10px;
            font-size: 0.96rem;
            margin: 0.55rem 0 0.85rem;
            border: 1px solid transparent;
        }
        .status-success {
            background: var(--green);
            color: #1e7e63;
        }
        .status-info {
            background: var(--blue);
            color: #2b73b6;
        }
        .atom-loader-shell {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0.8rem;
            min-height: 260px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(32, 178, 170, 0.14);
            border-radius: 24px;
            margin: 0.35rem 0 1.2rem;
        }
        .atom-loader-icon {
            font-size: 4.6rem;
            line-height: 1;
            color: #1fa49d;
            display: inline-block;
            animation: atom-spin 1.35s linear infinite;
            transform-origin: center;
        }
        .atom-loader-text {
            font-size: 1.02rem;
            color: #4e6e69;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        @keyframes atom-spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem 3rem;
            margin-bottom: 1.35rem;
        }
        .metric-item {
            display: flex;
            gap: 0.4rem;
            align-items: baseline;
            font-size: 1rem;
        }
        .metric-label {
            color: #17453f;
            font-weight: 700;
        }
        .metric-value {
            color: var(--text);
            font-weight: 500;
        }
        .pill-ok {
            background: var(--green);
            color: #1e7e63;
            padding: 1rem 1.1rem;
            border-radius: 10px;
            margin: 0.45rem 0 1.2rem;
        }
        .subtle-copy {
            color: var(--muted);
            font-size: 0.93rem;
        }
        .energy-card {
            font-size: 0.98rem;
            margin-bottom: 1rem;
        }
        .energy-value {
            font-size: 2rem;
            font-weight: 800;
            margin-top: 0.35rem;
        }
        .panel-card {
            background: var(--card);
            border: 1px solid rgba(32, 178, 170, 0.12);
            border-radius: 18px;
            padding: 1rem;
        }
        .small-caption {
            color: var(--muted);
            font-size: 0.84rem;
        }
        .input-block {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(32, 178, 170, 0.12);
            border-radius: 12px;
            padding: 0.75rem;
            margin-bottom: 0.9rem;
        }
        .upload-chip {
            background: transparent;
            border: 1px solid rgba(32, 178, 170, 0.18);
            border-radius: 12px;
            padding: 0.65rem 0.75rem;
            margin-top: 0.65rem;
        }
        .streamlit-expanderHeader {
            color: var(--text);
        }
        .stButton > button {
            background: linear-gradient(180deg, #24b8af, #1fa49d);
            color: white;
            border: 1px solid #1d9b94;
            border-radius: 10px;
            font-weight: 700;
        }
        .stButton > button:hover {
            border-color: #187f79;
            color: white;
        }
        .stTextInput > div > div > input,
        .stNumberInput input,
        .stSelectbox [data-baseweb="select"] > div,
        .stFileUploader > div,
        .stTextArea textarea {
            background: #ffffff !important;
            color: #153d38 !important;
            border: 1px solid #b7dfd8 !important;
            border-radius: 10px !important;
        }
        .stProgress > div > div > div > div {
            background-color: #4c96f0;
        }
        .stAlert {
            background: #ffffff;
            color: #153d38;
            border: 1px solid #c6e7e1;
        }
        .setup-shell {
            min-height: auto;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding-top: 0.15rem;
        }
        .setup-card {
            width: min(1180px, 94vw);
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(32, 178, 170, 0.14);
            border-radius: 30px;
            padding: 1.8rem 2.2rem 1.8rem;
            box-shadow: 0 24px 60px rgba(20, 69, 64, 0.08);
        }
        .setup-kicker {
            font-size: 4.4rem;
            line-height: 0.9;
            letter-spacing: -0.07em;
            font-weight: 900;
            color: #123f3b;
            margin-bottom: 0.5rem;
        }
        .setup-title {
            font-size: 1.55rem;
            line-height: 1.05;
            letter-spacing: -0.03em;
            font-weight: 800;
            color: #205853;
            margin-bottom: 0.65rem;
        }
        .setup-copy {
            font-size: 1.02rem;
            line-height: 1.6;
            color: #577d76;
            margin-bottom: 1.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def local_tool(name: str) -> Path | None:
    candidates = [
        Path("tools") / name,
        Path(".venv/bin") / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    resolved = shutil.which(name)
    return Path(resolved) if resolved else None


def model_metadata(model_path: Path) -> dict | None:
    metadata_path = model_path.with_suffix(".metadata.json")
    if metadata_path.exists():
        return read_json(metadata_path)
    return None


def save_uploaded_pdb(uploaded_file) -> Path:
    ensure_dir(UPLOAD_DIR)
    file_path = UPLOAD_DIR / uploaded_file.name
    file_path.write_bytes(uploaded_file.getbuffer())
    return file_path


def render_ligand_viewer(smiles: str, output_dir: Path) -> None:
    if py3Dmol is None:
        st.info("Install py3Dmol to enable 3D ligand visualization.")
        return
    try:
        ligand_sdf = write_smiles_3d(smiles, output_dir / "ligand_preview.sdf")
    except ChemistryDependencyError:
        st.warning(
            "RDKit is not installed — 3D ligand rendering is disabled. "
            "Install RDKit (see README) to enable ligand previews."
        )
        return
    viewer = py3Dmol.view(width=420, height=420)
    viewer.addModel(ligand_sdf.read_text(encoding="utf-8", errors="ignore"), "sdf")
    viewer.setStyle({"stick": {"colorscheme": "default"}, "sphere": {"scale": 0.28}})
    viewer.setBackgroundColor("#ffffff")
    viewer.zoomTo()
    components.html(viewer._make_html(), height=440)


def render_docking_viewer(receptor_path: Path | None, pose_path: Path | None) -> None:
    if py3Dmol is None:
        st.info("Install py3Dmol to enable 3D docking visualization.")
        return
    viewer = py3Dmol.view(width=700, height=420)
    if receptor_path and receptor_path.exists():
        receptor_format = "pdbqt" if receptor_path.suffix.lower() == ".pdbqt" else "pdb"
        viewer.addModel(receptor_path.read_text(encoding="utf-8", errors="ignore"), receptor_format)
        viewer.setStyle({"cartoon": {"color": "spectrum"}})
    if pose_path and pose_path.exists():
        viewer.addModel(pose_path.read_text(encoding="utf-8", errors="ignore"), "pdbqt")
        viewer.setStyle({"model": 1}, {"stick": {"colorscheme": "greenCarbon", "radius": 0.18}})
    viewer.setBackgroundColor("#ffffff")
    viewer.zoomTo()
    components.html(viewer._make_html(), height=440)


def render_property_grid(properties: dict) -> None:
    items = [
        ("Molecular Weight", f"{properties['molecular_weight']:.2f}"),
        ("LogP", f"{properties['logp']:.2f}"),
        ("H Bond Donors", str(properties["h_bond_donors"])),
        ("H Bond Acceptors", str(properties["h_bond_acceptors"])),
        ("Tpsa", f"{properties['tpsa']:.1f}"),
        ("Rotatable Bonds", str(properties["rotatable_bonds"])),
        ("Heavy Atoms", str(properties["heavy_atom_count"])),
    ]
    rows = []
    for label, value in items:
        rows.append(
            '<div class="metric-item">'
            f'<span class="metric-label">{label}:</span>'
            f'<span class="metric-value">{value}</span>'
            "</div>"
        )
    st.markdown(f'<div class="metric-grid">{"".join(rows)}</div>', unsafe_allow_html=True)


def build_receptor_selection(uploaded_file, preset_name: str) -> tuple[Path | None, str | None]:
    if uploaded_file is not None:
        saved_path = save_uploaded_pdb(uploaded_file)
        return saved_path, uploaded_file.name

    preset = RECEPTOR_PRESETS.get(preset_name)
    preset_path = first_existing_path(receptor_candidates(preset["filename"])) if preset else None
    if preset_path is not None:
        return preset_path, preset_path.name

    if DEFAULT_RECEPTOR_PATH.exists():
        return DEFAULT_RECEPTOR_PATH, DEFAULT_RECEPTOR_PATH.name
    return None, None


def sync_compound_inputs(section_prefix: str, receptor_preset_name: str) -> None:
    receptor_preset = RECEPTOR_PRESETS[receptor_preset_name]
    compound_key = f"{section_prefix}compound_preset_{receptor_preset_name}"
    smiles_key = f"{section_prefix}smiles_{receptor_preset_name}"
    compound_name_key = f"{section_prefix}compound_name_{receptor_preset_name}"
    marker_key = f"{compound_key}__last_synced"

    selected_compound = st.session_state.get(compound_key)
    if selected_compound not in receptor_preset["compound_presets"]:
        return

    if st.session_state.get(marker_key) != selected_compound:
        st.session_state[smiles_key] = receptor_preset["compound_presets"][selected_compound]
        st.session_state[compound_name_key] = selected_compound
        st.session_state[marker_key] = selected_compound


def api_health(base_url: str) -> bool:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/health", timeout=3)
        response.raise_for_status()
        return response.json().get("status") == "ok"
    except Exception:
        return False


def fetch_history_from_api(base_url: str, database: str, limit: int = 10) -> list[dict]:
    try:
        response = requests.get(
            f"{base_url.rstrip('/')}/history",
            params={"database": database, "limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


def analyze_via_api(
    *,
    base_url: str,
    compound_name: str,
    protein_name: str,
    smiles: str,
    model_path: str,
    workspace: str,
    database: str,
    receptor_file_path: Path | None,
) -> dict:
    if receptor_file_path is not None and receptor_file_path.exists():
        with receptor_file_path.open("rb") as receptor_stream:
            response = requests.post(
                f"{base_url.rstrip('/')}/upload-and-analyze",
                data={
                    "compound_name": compound_name,
                    "protein_name": protein_name,
                    "smiles": smiles,
                    "model_path": model_path,
                    "workspace": workspace,
                    "database": database,
                },
                files={"receptor_file": (receptor_file_path.name, receptor_stream, "chemical/x-pdb")},
                timeout=180,
            )
    else:
        response = requests.post(
            f"{base_url.rstrip('/')}/analyze",
            json={
                "compound_name": compound_name,
                "protein_name": protein_name,
                "smiles": smiles,
                "model_path": model_path,
                "workspace": workspace,
                "database": database,
            },
            timeout=180,
        )

    response.raise_for_status()
    return response.json()


def format_backend_error(exc: requests.RequestException) -> str:
    response = getattr(exc, "response", None)
    if response is None:
        return str(exc)

    detail = ""
    try:
        payload = response.json()
        detail = payload.get("detail") if isinstance(payload, dict) else ""
    except ValueError:
        detail = response.text.strip()

    if detail:
        return f"{response.status_code} {response.reason}: {detail}"
    return f"{response.status_code} {response.reason}"


def payload_section(result_payload: dict | None, key: str):
    if not result_payload or not isinstance(result_payload, dict):
        return None
    return result_payload.get(key)


def normalize_toxicity_payload(toxicity: dict | None) -> dict | None:
    if not toxicity:
        return None

    normalized = dict(toxicity)
    label = normalized.get("label")
    class_probabilities = normalized.get("class_probabilities")

    if not isinstance(class_probabilities, dict):
        probability = float(normalized.get("probability") or 0.0)
        if label == "Toxic":
            class_probabilities = {"Toxic": probability, "Non-toxic": 1.0 - probability}
        elif label == "Non-toxic":
            class_probabilities = {"Non-toxic": probability, "Toxic": 1.0 - probability}
        else:
            class_probabilities = {}
    else:
        class_probabilities = {
            str(name): float(value) for name, value in class_probabilities.items()
        }
        if label == "Toxic" and "Non-toxic" not in class_probabilities and "Toxic" in class_probabilities:
            class_probabilities["Non-toxic"] = 1.0 - class_probabilities["Toxic"]
        if label == "Non-toxic" and "Toxic" not in class_probabilities and "Non-toxic" in class_probabilities:
            class_probabilities["Toxic"] = 1.0 - class_probabilities["Non-toxic"]

    normalized["class_probabilities"] = class_probabilities
    if label in class_probabilities:
        normalized["probability"] = class_probabilities[label]
    return normalized


def render_atom_loader(placeholder) -> None:
    placeholder.markdown(
        """
        <div class="atom-loader-shell">
          <div class="atom-loader-icon">⚛</div>
          <div class="atom-loader-text">Analyzing molecule and protein...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_latest_result_from_history(history_rows: list[dict]) -> dict | None:
    if not history_rows:
        return None

    latest_row = history_rows[0]
    descriptors_json = latest_row.get("descriptors_json")
    if not descriptors_json:
        return None

    try:
        descriptors = json.loads(descriptors_json)
    except json.JSONDecodeError:
        return None

    toxicity = None
    if latest_row.get("toxicity_label"):
        toxicity = normalize_toxicity_payload({
            "label": latest_row["toxicity_label"],
            "probability": float(latest_row.get("toxicity_probability") or 0.0),
        })

    binding = summarize_binding(latest_row.get("binding_energy"), descriptors)

    return {
        "descriptors": descriptors,
        "toxicity": toxicity,
        "binding": binding.to_dict() if binding else None,
    }


inject_styles()

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "selected_receptor_path" not in st.session_state:
    st.session_state.selected_receptor_path = str(DEFAULT_RECEPTOR_PATH) if DEFAULT_RECEPTOR_PATH.exists() else ""
if "selected_receptor_preset" not in st.session_state:
    st.session_state.selected_receptor_preset = "1HSG"
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = API_BASE_URL_DEFAULT
if "app_started" not in st.session_state:
    st.session_state.app_started = False

latest_history = fetch_history_from_api(st.session_state.api_base_url, str(db_path), limit=10)
latest_saved_result = build_latest_result_from_history(latest_history)


if not st.session_state.app_started:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        .block-container { max-width: 100%; padding-top: 0.15rem; padding-bottom: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="setup-shell"><div class="setup-card">', unsafe_allow_html=True)
    st.markdown('<div class="setup-kicker">BindTox</div>', unsafe_allow_html=True)
    st.markdown('<div class="setup-title">Input Parameters</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="setup-copy">Choose the receptor, compound preset, and target details first. After that, proceed into the full analysis platform.</div>',
        unsafe_allow_html=True,
    )

    receptor_preset_name = st.selectbox(
        "Built-in Receptor",
        list(RECEPTOR_PRESETS),
        index=list(RECEPTOR_PRESETS).index(st.session_state.selected_receptor_preset),
        key="landing_receptor_preset",
    )
    receptor_preset = RECEPTOR_PRESETS[receptor_preset_name]

    compound_preset_name = st.selectbox(
        "Compound Preset",
        list(receptor_preset["compound_presets"]),
        key=f"landing_compound_preset_{receptor_preset_name}",
    )
    sync_compound_inputs("landing_", receptor_preset_name)
    smiles = st.text_input(
        "Ligand SMILES",
        receptor_preset["compound_presets"][compound_preset_name],
        key=f"landing_smiles_{receptor_preset_name}",
    )
    compound_name = st.text_input(
        "Compound Name",
        compound_preset_name,
        key=f"landing_compound_name_{receptor_preset_name}",
    )
    protein_name = st.text_input(
        "Target Protein",
        receptor_preset["protein_name"],
        key=f"landing_protein_name_{receptor_preset_name}",
    )

    selected_receptor, _ = build_receptor_selection(None, receptor_preset_name)
    if selected_receptor is not None:
        st.session_state.selected_receptor_path = str(selected_receptor)

    if st.button("Proceed", type="primary", use_container_width=True, key="landing_proceed"):
        st.session_state.selected_receptor_preset = receptor_preset_name
        st.session_state[f"compound_preset_{receptor_preset_name}"] = compound_preset_name
        st.session_state[f"smiles_{receptor_preset_name}"] = smiles
        st.session_state[f"compound_name_{receptor_preset_name}"] = compound_name
        st.session_state[f"protein_name_{receptor_preset_name}"] = protein_name
        st.session_state.app_started = True
        st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()


with st.sidebar:
    st.markdown("## Input Parameters")
    st.markdown("### Choose Protein PDB")
    receptor_preset_name = st.selectbox(
        "Built-in Receptor",
        list(RECEPTOR_PRESETS),
        index=list(RECEPTOR_PRESETS).index(st.session_state.selected_receptor_preset),
    )
    st.session_state.selected_receptor_preset = receptor_preset_name
    receptor_preset = RECEPTOR_PRESETS[receptor_preset_name]

    compound_preset_name = st.selectbox(
        "Compound Preset",
        list(receptor_preset["compound_presets"]),
        key=f"compound_preset_{receptor_preset_name}",
    )
    sync_compound_inputs("", receptor_preset_name)
    smiles = st.text_input(
        "Ligand SMILES",
        receptor_preset["compound_presets"][compound_preset_name],
        key=f"smiles_{receptor_preset_name}",
    )
    compound_name = st.text_input(
        "Compound Name",
        compound_preset_name,
        key=f"compound_name_{receptor_preset_name}",
    )
    protein_name = st.text_input(
        "Target Protein",
        receptor_preset["protein_name"],
        key=f"protein_name_{receptor_preset_name}",
    )

    selected_receptor, receptor_name = build_receptor_selection(None, receptor_preset_name)
    if selected_receptor is not None:
        st.session_state.selected_receptor_path = str(selected_receptor)

    dataset_path = str(DATASET_PATH_DEFAULT)
    model_path = str(MODEL_PATH_DEFAULT)
    st.markdown("### Advanced")
    dataset_path = st.text_input("Dataset CSV", dataset_path)
    model_path = st.text_input("Model Output", model_path)
    if st.button("Train Toxicity Model"):
        result = train_toxicity_model(Path(dataset_path), Path(model_path))
        st.success(f"Model trained with accuracy {result.accuracy:.2%}")

    st.markdown("### Upload Protein PDB")
    uploaded_pdb = st.file_uploader("Upload Protein PDB", type=["pdb"], label_visibility="collapsed")
    selected_receptor, receptor_name = build_receptor_selection(uploaded_pdb, receptor_preset_name)
    if selected_receptor is not None:
        st.session_state.selected_receptor_path = str(selected_receptor)
        st.markdown(
            f"""
            <div class="upload-chip">
              <div style="font-weight:700;">{receptor_name}</div>
              <div class="small-caption">{round(selected_receptor.stat().st_size / 1024, 1)} KB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("Upload a `.pdb` file to enable docking.")

st.markdown('<h1 class="hero-title">Drug-Protein Binding & Toxicity Prediction Platform</h1>', unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

detected_box = None
selected_receptor_path = Path(st.session_state.selected_receptor_path) if st.session_state.selected_receptor_path else None
if selected_receptor_path and selected_receptor_path.exists():
    try:
        detected_box = detect_binding_pocket(selected_receptor_path)
    except Exception:
        detected_box = None

with st.container():
    col_left, col_right = st.columns([1.05, 1.0], gap="large")

    with col_left:
        st.markdown('<div class="section-title">Chemical Analysis</div>', unsafe_allow_html=True)
        try:
            properties = calculate_properties(smiles).to_dict()
        except ChemistryDependencyError:
            # RDKit is not installed — provide a minimal fallback so the UI remains usable
            st.warning(
                "RDKit is not installed. Chemical property calculation is disabled. "
                "Install RDKit (see README) to enable full chemistry features."
            )
            properties = {
                "molecular_weight": 0.0,
                "logp": 0.0,
                "h_bond_donors": 0,
                "h_bond_acceptors": 0,
                "tpsa": 0.0,
                "rotatable_bonds": 0,
                "heavy_atom_count": 0,
                "lipinski_pass": False,
                "lipinski_violations": [],
            }
        render_property_grid(properties)

        st.markdown("### Lipinski Rule Validation")
        if properties["lipinski_pass"]:
            st.markdown('<div class="pill-ok">Passes Lipinski\'s Rule of Five</div>', unsafe_allow_html=True)
        else:
            violations = ", ".join(properties["lipinski_violations"])
            st.error(f"Lipinski review needed: {violations}")

        toxicity_box = st.container()
        result_payload = st.session_state.analysis_result
        with toxicity_box:
            st.markdown("### Toxicity Prediction")
            active_result = result_payload or latest_saved_result
            docking_for_toxicity = payload_section(active_result, "docking")
            toxicity = normalize_toxicity_payload(payload_section(active_result, "toxicity"))
            if docking_for_toxicity and toxicity:
                status_color = "#ef7d7d" if toxicity["label"] == "Toxic" else "#8be0a6"
                st.markdown(
                    f"Status: <span style='color:{status_color}; font-weight:700;'>{toxicity['label']}</span>",
                    unsafe_allow_html=True,
                )
                predicted_probability = float(toxicity["class_probabilities"].get(toxicity["label"], 0.0))
                toxic_probability = float(toxicity["class_probabilities"].get("Toxic", 0.0))
                st.progress(min(max(predicted_probability, 0.0), 1.0))
                st.caption(f"{toxicity['label']} Confidence: {predicted_probability:.4f}")
                st.caption(f"Toxicity Risk: {toxic_probability:.4f}")
            else:
                st.caption("Complete docking to show toxicity prediction.")

        st.markdown("### Binding Analysis")
        binding = payload_section(result_payload, "binding") or payload_section(latest_saved_result, "binding")
        if binding:
            st.markdown(
                f"""
                <div class="panel-card">
                  <div><strong>Affinity Band:</strong> {binding['affinity_band']}</div>
                  <div style="margin-top:0.5rem;"><strong>Interpretation:</strong> {binding['interpretation']}</div>
                  <div style="margin-top:0.5rem;"><strong>Likely Interactions:</strong> {", ".join(binding['likely_interactions'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption("Binding interpretation appears after docking.")

        st.markdown("### Ligand 3D Structure")
        render_ligand_viewer(smiles, Path("artifacts/ui_previews"))

    with col_right:
        st.markdown('<div class="section-title">Docking & Binding</div>', unsafe_allow_html=True)

        if st.button("Run Docking Simulation", type="primary", disabled=selected_receptor_path is None):
            active_box = detected_box or PocketBox(center_x=0.0, center_y=0.0, center_z=0.0, size_x=20.0, size_y=20.0, size_z=20.0)
            loading_placeholder = st.empty()
            render_atom_loader(loading_placeholder)
            try:
                result = analyze_via_api(
                    base_url=st.session_state.api_base_url,
                    compound_name=compound_name,
                    protein_name=protein_name,
                    smiles=smiles,
                    model_path=str(model_path),
                    workspace="artifacts/dashboard_run",
                    database=str(db_path),
                    receptor_file_path=selected_receptor_path,
                )
                result.setdefault("preprocessing", {})
                result["preprocessing"]["frontend_detected_pocket"] = {
                    "center_x": active_box.center_x,
                    "center_y": active_box.center_y,
                    "center_z": active_box.center_z,
                }
                st.session_state.analysis_result = result
                st.rerun()
            except requests.RequestException as exc:
                st.error(f"Docking request failed: {format_backend_error(exc)}")
                st.info("Start the backend first with: PYTHONPATH=src python -m bindtox.cli serve-api --host 0.0.0.0 --port 8000 (or set BINDTOX_API_URL to the backend URL)")
            except Exception as exc:
                st.error(f"Docking failed unexpectedly: {exc}")
            finally:
                loading_placeholder.empty()

        result_payload = st.session_state.analysis_result
        docking = payload_section(result_payload, "docking")
        if docking:
            st.markdown("### Docking Results")
            st.markdown(
                f"""
                <div class="energy-card">
                  <div class="small-caption">Binding Energy</div>
                  <div class="energy-value">{docking['binding_energy']:.3f} kcal/mol</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("### Docking Pose Visualization")
            render_docking_viewer(Path(docking["receptor_path"]), Path(docking["output_pose_path"]))
        else:
            st.caption("Run docking to see binding energy and pose visualization.")

model_meta = model_metadata(Path(model_path))
if model_meta:
    with st.expander("Live Model Metrics"):
        st.write(
            {
                "validation_accuracy": model_meta["accuracy"],
                "train_size": model_meta["train_size"],
                "test_size": model_meta["test_size"],
                "vina_available": bool(local_tool("vina")),
                "ligand_preparation": bool(local_tool("mk_prepare_ligand.py")),
                "receptor_preparation": bool(local_tool("mk_prepare_receptor.py")),
            }
        )
        st.text(model_meta["report"])
