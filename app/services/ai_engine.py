"""C10 -- Layanan inferensi AI GATNN-DNN (menggantikan versi GCNConv lama).

Perbaikan enam cacat dari versi `master` lama (terdokumentasi di
ml/reports/C12_dokumentasi_model.md):
1. `GCNConv` -> `GATv2Conv` (`hepatwin_ml.models.gatnn_dnn.GatnnDnn`, C4/C6).
2. `nn.Sigmoid()` dihapus dari `forward()` model -- sigmoid HANYA di sini
   (`predict_dili_risk`), setelah kalibrasi (C7).
3. Node feature 34-dim penuh (`hepatwin_ml.features.graph`, C3), bukan 4
   nilai riil di-pad nol jadi 9.
4. `return 0.5` diam-diam DIHAPUS -- model tidak termuat/gagal ->
   `HTTPException(503)` eksplisit (`_require_ready`). Cacat integritas
   ilmiah, bukan sekadar bug.
5. SHAP di-batch satu forward pass (`hepatwin_ml.explain`, C8), bukan loop
   serial per sampel sintetis seperti versi lama.
6. `SMARTS_PATTERNS` versi terkoreksi -- diimpor dari `hepatwin_ml.features.smarts`
   (satu-satunya sumber, dipakai juga saat training), TIDAK didefinisikan
   ulang secara lokal di sini seperti versi lama (mencegah drift).

Featurization/model/explainability diimpor dari `ml/` (`hepatwin_ml`, terpasang
`-e ./ml` di `requirements.txt` root), BUKAN diduplikasi -- prinsip C10:
"Duplikasi kode fitur adalah sumber klasik ketidakcocokan training<->inferensi."

Kebijakan statis (C9): model dimuat SEKALI di `__init__`, `model.eval()`
dipanggil, seluruh forward pass di bawah `torch.no_grad()`. Tidak ada jalur
kode yang memanggil `.backward()`/`optimizer.step()`/menulis ulang bobot.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from fastapi import HTTPException, status
from rdkit import Chem
from torch_geometric.data import Batch

from hepatwin_ml.data.standardize import standardize
from hepatwin_ml.explain import explain
from hepatwin_ml.features.fingerprints import dnn_feature_vector
from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

logger = logging.getLogger(__name__)

DEFAULT_MODEL_VERSION = "gatnn-dnn-fixmodel-v1"
# Fallback hyperparameter final (ml/reports/C6_train_summary.md) -- dipakai
# hanya bila file metadata tidak ada/gagal dibaca; nilai sesungguhnya SELALU
# dibaca dari model_gatnn_dnn_metadata.json (C6) bila tersedia.
_FALLBACK_HIDDEN = 64
_FALLBACK_DROPOUT = 0.2


class HybridAIEngine:
    """Model AI GATNN-DNN (GATv2Conv + DNN hybrid, PyTorch Geometric).

    Instansiasi sekali per proses (lihat `app/api/dependencies.py`), bukan
    per-request -- memuat ulang bobot model tiap request akan melanggar
    anggaran latensi PRD UC-02 (<=5 detik total).
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.device = torch.device("cpu")  # deployment tidak menjamin GPU tersedia
        self.model: Optional[GatnnDnn] = None
        self.calibrator = None
        self.model_version = DEFAULT_MODEL_VERSION
        self.score_is_calibrated = False
        self.ready = False

        self._load_model()
        self._load_calibrator()
        self._warm_up()

        logger.info(
            "HybridAIEngine diinisialisasi: ready=%s model_version=%s score_is_calibrated=%s path=%s",
            self.ready, self.model_version, self.score_is_calibrated, self.model_path,
        )

    def _warm_up(self) -> None:
        """Jalankan satu inferensi + explain() dummy saat startup proses
        (main thread) supaya lazy-init PyTorch/RDKit di thread INI dibayar
        sebelum request nyata pertama. TERBUKTI mempercepat pemanggilan
        LANGSUNG (di luar HTTP/executor) dari ~6 detik ke <10ms -- tapi
        TIDAK cukup sendirian untuk request HTTP nyata (lihat warm-up
        tambahan di app/main.py startup event + catatan jujur di sana soal
        sisa latensi request pertama yang akar masalahnya belum tuntas
        ditemukan). Dipertahankan karena tetap mengurangi sebagian biaya
        dan tidak merugikan."""
        if not self.ready:
            return
        try:
            self.predict_dili_risk("C")  # metana -- molekul valid paling sederhana
            self.get_shap_detail("C")
        except Exception as exc:  # noqa: BLE001 -- warm-up gagal tidak boleh menggagalkan startup
            logger.warning("Warm-up inferensi gagal (non-fatal, lanjut startup): %s", exc)

    @property
    def model_status(self) -> str:
        return "trained" if self.ready else "unavailable"

    def _load_model(self) -> None:
        if not self.model_path:
            logger.error("AI_MODEL_PATH tidak diset -- HybridAIEngine tidak bisa memuat model.")
            return

        model_file = Path(self.model_path)
        metadata_file = model_file.with_name(model_file.stem + "_metadata.json")

        hidden, dropout = _FALLBACK_HIDDEN, _FALLBACK_DROPOUT
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                hp = metadata.get("hyperparameters", {})
                hidden = hp.get("hidden", hidden)
                dropout = hp.get("dropout", dropout)
                self.model_version = metadata.get("model_version", self.model_version)
            except Exception as exc:  # noqa: BLE001 -- gagal baca metadata bukan alasan crash total
                logger.warning("Gagal membaca metadata model %s: %s -- pakai fallback hyperparameter.", metadata_file, exc)

        if not model_file.exists():
            logger.error(
                "Artefak model tidak ditemukan di %s -- HybridAIEngine TIDAK siap "
                "(predict_dili_risk akan menolak dengan 503, bukan skor palsu).",
                model_file,
            )
            return

        try:
            model = GatnnDnn(hidden=hidden, dropout=dropout)
            state_dict = torch.load(model_file, map_location=self.device, weights_only=True)
            model.load_state_dict(state_dict)
            model.eval()  # kebijakan statis C9 -- model tidak pernah dikembalikan ke train()
            self.model = model
            self.ready = True
        except Exception as exc:  # noqa: BLE001 -- dicatat, engine tetap "not ready" (bukan crash proses)
            logger.error("Gagal memuat state_dict model dari %s: %s", model_file, exc)
            self.model = None
            self.ready = False

    def _load_calibrator(self) -> None:
        if not self.model_path:
            return
        calibrator_file = Path(self.model_path).with_name("calibrator_gatnn_dnn.pkl")
        if not calibrator_file.exists():
            logger.warning(
                "Kalibrator tidak ditemukan di %s -- dili_score TIDAK terkalibrasi "
                "(sigmoid mentah, score_is_calibrated=False).",
                calibrator_file,
            )
            return
        try:
            with open(calibrator_file, "rb") as f:
                self.calibrator = pickle.load(f)
            self.score_is_calibrated = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gagal memuat kalibrator dari %s: %s -- lanjut tanpa kalibrasi.", calibrator_file, exc)

    def _require_ready(self) -> None:
        """Cacat #4 (C10): TIDAK ADA fallback skor 0.5 diam-diam. Model tidak
        termuat -> 503 eksplisit, selalu, tanpa kecuali."""
        if not self.ready or self.model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Model AI GATNN-DNN tidak tersedia (artefak gagal dimuat saat startup). "
                    "Tidak ada prediksi yang dapat dikembalikan."
                ),
            )

    def _standardize_or_422(self, smiles: str):
        std = standardize(smiles) if smiles else None
        if std is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"SMILES tidak valid atau gagal diparse RDKit: {smiles!r}",
            )
        return std

    def predict_dili_risk(self, smiles: str) -> float:
        """SMILES -> P(DILI) terkalibrasi (float, 0..1).

        `HTTPException(503)` bila model tidak termuat, `HTTPException(422)`
        bila SMILES tidak valid -- TIDAK PERNAH diam-diam mengembalikan 0.5.
        """
        self._require_ready()
        std = self._standardize_or_422(smiles)

        graph_data = smiles_to_graph(std.canonical_smiles)
        mol = Chem.MolFromSmiles(std.canonical_smiles)
        fingerprint = torch.tensor(dnn_feature_vector(mol), dtype=torch.float).unsqueeze(0)

        batch = Batch.from_data_list([graph_data])
        batch.fingerprint = fingerprint
        with torch.no_grad():
            logit = self.model(batch)
            prob = torch.sigmoid(logit).item()

        if self.calibrator is not None:
            prob = float(self.calibrator.predict([prob])[0])

        return float(prob)

    def get_shap_detail(self, smiles: str) -> Dict[str, Any]:
        """SMILES -> keluaran `explain()` C8 penuh: method, groups (gugus
        SMARTS + atom_indices), atoms (atribusi per-atom), smiles_used."""
        self._require_ready()
        std = self._standardize_or_422(smiles)
        return explain(self.model, std.canonical_smiles, std.inchikey)

    def get_explainability(self, smiles: str) -> List[str]:
        """Kompatibilitas mundur untuk `explainability_shap: List[str]`
        (skema lama) -- nama gugus saja, diturunkan dari `get_shap_detail()`
        (satu sumber, tidak menghitung ulang secara terpisah)."""
        detail = self.get_shap_detail(smiles)
        return [g["name"] for g in detail["groups"]]
