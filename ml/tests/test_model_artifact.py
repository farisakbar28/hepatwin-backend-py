"""C6 -- test artefak model terlatih (butuh ml/models/model_gatnn_dnn.pt dari
ml/scripts/run_train.py, di-skip otomatis bila belum pernah dijalankan)."""
import json
from pathlib import Path

import pytest
import torch

from hepatwin_ml.models.gatnn_dnn import GatnnDnn

_REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = _REPO_ROOT / "ml" / "models" / "model_gatnn_dnn.pt"
METADATA_PATH = _REPO_ROOT / "ml" / "models" / "model_gatnn_dnn_metadata.json"

pytestmark = pytest.mark.skipif(
    not (MODEL_PATH.exists() and METADATA_PATH.exists()),
    reason="Jalankan ml/scripts/run_train.py dulu",
)


@pytest.fixture(scope="module")
def metadata() -> dict:
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def test_model_state_dict_loads_into_matching_architecture(metadata):
    hp = metadata["hyperparameters"]
    model = GatnnDnn(hidden=hp["hidden"], dropout=hp["dropout"])
    state_dict = torch.load(MODEL_PATH, weights_only=True)
    model.load_state_dict(state_dict)  # raises on shape/key mismatch
    model.eval()


def test_metadata_hyperparameters_match_project_spec(metadata):
    hp = metadata["hyperparameters"]
    assert hp["lr"] == 0.0005
    assert hp["hidden"] == 64
    assert hp["dropout"] == 0.2
    assert hp["weight_decay"] == 1e-4


def test_metadata_records_split_manifest_hash_for_provenance(metadata):
    assert len(metadata["split_manifest_sha256"]) == 64  # sha256 hex digest


def test_determinism_check_passed(metadata):
    assert metadata["determinism_check"]["identical"] is True


def test_checkpoint_is_not_random_weights(metadata):
    """AC C6: bukan bobot acak -- val_auc harus jelas di atas 0.5 (tebak acak)."""
    assert metadata["val_metrics_production_seed"]["auc_roc"] > 0.55
