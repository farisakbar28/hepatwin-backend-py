"""Mesin AI DILI (GATNN-DNN, Arm A) -- ditulis ulang total untuk branch upscale.

K1 (keputusan Ketua Tim, UPSCALE.md): arsitektur GATNN menggantikan HybridGNN/
GCNConv versi master. Model & fitur kimia (standardize, graf, fingerprint,
SMARTS) diimpor dari package `hepatwin_ml` (ml/) supaya kode training dan
inference memakai definisi fitur yang identik -- tidak diduplikasi.

Larangan (UPSCALE.md SS10): TIDAK ADA silent fallback ke skor 0.5. Bila
artefak model tidak ada/gagal dimuat, engine ini tidak "ready" dan endpoint
WAJIB membalas 503, bukan skor default.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import List, Optional

import torch
from rdkit import Chem
from torch_geometric.data import Batch

from hepatwin_ml.data.standardize import standardize
from hepatwin_ml.explain import explain_smarts_contribution
from hepatwin_ml.features.fingerprints import dnn_feature_vector
from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

logger = logging.getLogger(__name__)


class ModelNotReadyError(Exception):
    """Artefak model tidak ada / gagal dimuat -- endpoint wajib balas 503."""


class HybridAIEngine:
    """Nama kelas dipertahankan (dipakai simulation_orchestrator.py) meski
    arsitektur di baliknya sekarang GATNN-DNN murni, bukan hybrid GCN lama."""

    def __init__(self, model_dir: Optional[str] = None):
        self.ready = False
        self.model: Optional[GatnnDnn] = None
        self.calibrator = None
        self.metadata: dict = {}

        base_dir = Path(model_dir) if model_dir else Path(__file__).resolve().parent.parent / "models"
        model_path = base_dir / "model_arm_a.pt"
        calibrator_path = base_dir / "calibrator_arm_a.pkl"
        metadata_path = base_dir / "model_arm_a_metadata.json"

        if not (model_path.exists() and calibrator_path.exists() and metadata_path.exists()):
            logger.error("Artefak model tidak lengkap di %s -- engine TIDAK ready", base_dir)
            return

        try:
            self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            model = GatnnDnn()
            model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
            model.eval()
            self.model = model
            with open(calibrator_path, "rb") as f:
                self.calibrator = pickle.load(f)
            self.ready = True
            logger.info(
                "Model %s dimuat (kalibrator=%s)", self.metadata.get("model_version"), self.calibrator.method
            )
        except Exception:
            logger.exception("Gagal memuat artefak model dari %s", base_dir)
            self.ready = False

    def _require_ready(self) -> None:
        if not self.ready:
            raise ModelNotReadyError("Model AI belum siap atau artefak tidak ditemukan")

    def validate_smiles(self, smiles: str) -> bool:
        if not smiles or not isinstance(smiles, str):
            return False
        std = standardize(smiles)
        return std is not None and std.eligible

    def predict_dili_risk(self, smiles: str) -> float:
        """SMILES tervalidasi -> skor risiko DILI TERKALIBRASI (0-1).

        Melempar ModelNotReadyError bila artefak tidak dimuat, ValueError bila
        SMILES tidak valid/di luar cakupan model -- TIDAK PERNAH diam-diam
        mengembalikan 0.5 (UPSCALE.md SS10).
        """
        self._require_ready()
        std = standardize(smiles)
        if std is None or not std.eligible:
            reason = std.reject_reason if std else "gagal parse RDKit"
            raise ValueError(f"SMILES tidak valid/di luar cakupan model ({reason}): {smiles!r}")

        graph_data = smiles_to_graph(std.canonical_smiles)
        mol = Chem.MolFromSmiles(std.canonical_smiles)
        fingerprint = dnn_feature_vector(mol)
        graph_data.fingerprint = torch.tensor(fingerprint, dtype=torch.float).unsqueeze(0)
        batch = Batch.from_data_list([graph_data])

        with torch.no_grad():
            logit = self.model(batch)
        raw_prob = torch.sigmoid(logit).numpy()
        calibrated = self.calibrator.predict(raw_prob)
        return float(calibrated[0])

    def get_explainability(self, smiles: str) -> List[str]:
        """Daftar nama pola SMARTS yang berkontribusi POSITIF terhadap skor.

        [KEPUTUSAN AI -- PENDING REVIEW FARMASI, EXECUTION_PLAN_UPSCALE.md
        SS14.1 gerbang B5]: nama pola belum divalidasi Farmasi.
        """
        self._require_ready()
        std = standardize(smiles)
        if std is None or not std.eligible:
            return []
        result = explain_smarts_contribution(self.model, std.canonical_smiles, std.inchikey)
        contributing = [name for name, val in result["contributions"].items() if val > 0.001]
        if not contributing:
            contributing = ["Tidak ada pola struktural dominan terdeteksi"]
        return contributing

    @property
    def model_version(self) -> str:
        return self.metadata.get("model_version", "unknown")

    @property
    def internal_cv_auc(self) -> Optional[float]:
        return self.metadata.get("internal_cv_auc_l1_random")

    @property
    def score_is_calibrated(self) -> bool:
        return self.ready and self.calibrator is not None
