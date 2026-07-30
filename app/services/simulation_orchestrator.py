from fastapi import HTTPException
from app.models.schemas import SimulationRequest, SimulationResponse
from app.services.pkpd_engine import AcetaminophenPKPDEngine
from app.services.ai_engine import HybridAIEngine, ModelNotReadyError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# SMILES kanonik nyata -- bukan lagi placeholder mock (UPSCALE.md branch upscale).
PARACETAMOL_SMILES = "CC(=O)Nc1ccc(O)cc1"
# [KEPUTUSAN AI -- PENDING REVIEW FARMASI, EXECUTION_PLAN_UPSCALE.md SS14.1 gerbang B4]:
# amox_clav memakai SMILES amoxicillin saja (fragmen utama), representasi kombinasi
# clavulanate ditolak pipeline standardisasi (MixtureError). Skor karenanya adalah
# proksi dari komponen amoxicillin, BUKAN sinyal gabungan Augmentin yang sebenarnya.
AMOX_CLAV_SMILES = "CC1(C)S[C@@H]2[C@H](NC(=O)[C@H](N)c3ccc(O)cc3)C(=O)N2[C@H]1C(=O)O"


class SimulationOrchestrator:
    def __init__(self):
        self.pkpd_engine = AcetaminophenPKPDEngine()
        self.ai_engine = HybridAIEngine(model_dir=settings.AI_MODEL_DIR)

    def handle_request(self, req: SimulationRequest) -> SimulationResponse:
        mode = req.mode
        dose = req.dose_mg_kg if req.dose_mg_kg is not None else 15.0

        compound_id = req.compound_id
        smiles = req.smiles_string

        try:
            if mode == "edukasi_mendalam":
                if compound_id not in ["paracetamol", "amox_clav"]:
                    raise HTTPException(status_code=400, detail="compound_id harus 'paracetamol' atau 'amox_clav'")

                if compound_id == "paracetamol":
                    return self._simulate_paracetamol(dose)
                elif compound_id == "amox_clav":
                    return self._simulate_amox_clav(dose)

            else:  # triase_umum
                if not smiles:
                    raise HTTPException(status_code=400, detail="smiles_string wajib untuk mode triase_umum")

                if not self.ai_engine.validate_smiles(smiles):
                    raise HTTPException(status_code=400, detail="smiles_string tidak valid")
                return self._simulate_triase(smiles)
        except ModelNotReadyError as exc:
            logger.error("Model AI tidak siap: %s", exc)
            raise HTTPException(status_code=503, detail="Model AI belum siap / artefak tidak ditemukan") from exc

    def _risk_level(self, score: float) -> str:
        if score > 0.66:
            return "high"
        if score >= 0.33:
            return "medium"
        return "low"

    def _simulate_paracetamol(self, dose: float) -> SimulationResponse:
        time_series = self.pkpd_engine.simulate_napqi_gsh_dynamics(dose)
        nomogram = self.pkpd_engine.get_nomogram_data(dose)
        score = self.ai_engine.predict_dili_risk(PARACETAMOL_SMILES)

        return SimulationResponse(
            mode="edukasi_mendalam",
            compound_name="Paracetamol",
            input_smiles=None,
            dose_mg_kg=dose,
            DILI_score=score,
            risk_level=self._risk_level(score),
            damage_severity=min(1.0, dose / 150.0),  # Simplifikasi proporsional dosis
            compound_class="dose_dependent",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis.",
            disclaimer_permanent="HepaTwin adalah alat bantu edukasi dan triase awal, BUKAN pengganti uji toksisitas atau keputusan klinis.",
            disclaimer_hideable=True,
            affected_zone="Zone_3",
            supports_micro_zoom=True,
            explainability=self.ai_engine.get_explainability(PARACETAMOL_SMILES),
            visual_pattern="centrilobular_necrosis",
            time_series_pkpd=time_series,
            nomogram_data=nomogram,
            model_version=self.ai_engine.model_version,
            model_status="ready" if self.ai_engine.ready else "unavailable",
            score_is_calibrated=self.ai_engine.score_is_calibrated,
            internal_cv_auc=self.ai_engine.internal_cv_auc,
        )

    def _simulate_amox_clav(self, dose: float) -> SimulationResponse:
        score = self.ai_engine.predict_dili_risk(AMOX_CLAV_SMILES)

        return SimulationResponse(
            mode="edukasi_mendalam",
            compound_name="Amoxicillin-Clavulanate",
            input_smiles=None,
            dose_mg_kg=dose,
            DILI_score=score,
            risk_level=self._risk_level(score),
            damage_severity=score,
            compound_class="idiosyncratic",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis. "
            "Skor berbasis komponen amoxicillin saja (lihat catatan B4 di kode).",
            disclaimer_permanent="HepaTwin adalah alat bantu edukasi dan triase awal, BUKAN pengganti uji toksisitas atau keputusan klinis.",
            disclaimer_hideable=True,
            affected_zone="Portal_Periportal",
            supports_micro_zoom=True,
            explainability=self.ai_engine.get_explainability(AMOX_CLAV_SMILES),
            visual_pattern="portal_inflammation",
            time_series_pkpd=None,
            nomogram_data=None,
            model_version=self.ai_engine.model_version,
            model_status="ready" if self.ai_engine.ready else "unavailable",
            score_is_calibrated=self.ai_engine.score_is_calibrated,
            internal_cv_auc=self.ai_engine.internal_cv_auc,
        )

    def _simulate_triase(self, smiles: str) -> SimulationResponse:
        score = self.ai_engine.predict_dili_risk(smiles)

        return SimulationResponse(
            mode="triase_umum",
            compound_name=None,
            input_smiles=smiles,
            dose_mg_kg=None,
            DILI_score=score,
            risk_level=self._risk_level(score),
            damage_severity=score,
            compound_class="unknown_general",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis.",
            disclaimer_permanent="Skor ini adalah estimasi awal berbasis model riset (AUC internal cross-validation ~0,73-0,74), BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat.",
            disclaimer_hideable=False,
            affected_zone="Macro_Generic",
            supports_micro_zoom=False,
            explainability=self.ai_engine.get_explainability(smiles),
            visual_pattern="heatmap_generik",
            time_series_pkpd=None,
            nomogram_data=None,
            model_version=self.ai_engine.model_version,
            model_status="ready" if self.ai_engine.ready else "unavailable",
            score_is_calibrated=self.ai_engine.score_is_calibrated,
            internal_cv_auc=self.ai_engine.internal_cv_auc,
        )
