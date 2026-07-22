import logging

from app.core.config import settings
from app.core.errors import RequestIncompleteError, SmilesInvalidError
from app.models.schemas import SimulationRequest, SimulationResponse
from app.services.ai_engine import HybridAIEngine
from app.services.pkpd_engine import AcetaminophenPKPDEngine

logger = logging.getLogger(__name__)

class SimulationOrchestrator:
    def __init__(self):
        self.pkpd_engine = AcetaminophenPKPDEngine()
        self.ai_engine = HybridAIEngine(model_path=settings.AI_MODEL_PATH)

    def handle_request(self, req: SimulationRequest) -> SimulationResponse:
        mode = req.mode
        dose = req.dose_mg_kg if req.dose_mg_kg is not None else 15.0
        
        compound_id = req.compound_id
        smiles = req.smiles_string

        if mode == "edukasi_mendalam":
            if compound_id not in ["paracetamol", "amox_clav"]:
                raise RequestIncompleteError("compound_id harus 'paracetamol' atau 'amox_clav'")

            if settings.MOCK_MODE:
                return self._simulate_mock(req, dose)

            if compound_id == "paracetamol":
                return self._simulate_paracetamol(dose)
            elif compound_id == "amox_clav":
                return self._simulate_amox_clav(dose)

        else: # triase_umum
            if not smiles:
                raise RequestIncompleteError("smiles_string wajib untuk mode triase_umum")

            if not self.ai_engine.validate_smiles(smiles):
                raise SmilesInvalidError("smiles_string tidak valid")

            if settings.MOCK_MODE:
                return self._simulate_mock(req, dose)

            return self._simulate_triase(smiles)

    def _simulate_paracetamol(self, dose: float) -> SimulationResponse:
        time_series = self.pkpd_engine.simulate_napqi_gsh_dynamics(dose)
        nomogram = self.pkpd_engine.get_nomogram_data(dose)
        score = self.ai_engine.predict_dili_risk("paracetamol_mock")
        
        risk_level = "low"
        if score > 0.66:
            risk_level = "high"
        elif score >= 0.33:
            risk_level = "medium"
            
        return SimulationResponse(
            mode="edukasi_mendalam",
            compound_name="Paracetamol",
            input_smiles=None,
            dose_mg_kg=dose,
            DILI_score=score,
            risk_level=risk_level,
            damage_severity=min(1.0, dose / 150.0), # Simplifikasi proporsional dosis
            compound_class="dose_dependent",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis.",
            disclaimer_permanent="HepaTwin adalah alat bantu edukasi dan triase awal, BUKAN pengganti uji toksisitas atau keputusan klinis.",
            disclaimer_hideable=True,
            affected_zone="Zone_3",
            supports_micro_zoom=True,
            explainability=self.ai_engine.get_explainability("CC(=O)NC1=CC=C(O)C=C1"),
            visual_pattern="centrilobular_necrosis",
            time_series_pkpd=time_series,
            nomogram_data=nomogram,
            model_status=self.ai_engine.model_status
        )

    def _simulate_amox_clav(self, dose: float) -> SimulationResponse:
        score = self.ai_engine.predict_dili_risk("amox_mock")
        # Use the correct Amoxicillin SMILES string for SHAP explainability
        amox_smiles = "CC1(C)SC2C(NC(=O)C(N)c3ccc(O)cc3)C(=O)N12"
        
        risk_level = "low"
        if score > 0.66:
            risk_level = "high"
        elif score >= 0.33:
            risk_level = "medium"
            
        return SimulationResponse(
            mode="edukasi_mendalam",
            compound_name="Amoxicillin-Clavulanate",
            input_smiles=None,
            dose_mg_kg=dose,
            DILI_score=score,
            risk_level=risk_level,
            damage_severity=score, # Damage driven by AI score
            compound_class="idiosyncratic",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis.",
            disclaimer_permanent="HepaTwin adalah alat bantu edukasi dan triase awal, BUKAN pengganti uji toksisitas atau keputusan klinis.",
            disclaimer_hideable=True,
            affected_zone="Portal_Periportal",
            supports_micro_zoom=True,
            explainability=self.ai_engine.get_explainability(amox_smiles),
            visual_pattern="portal_inflammation",
            time_series_pkpd=None,
            nomogram_data=None,
            model_status=self.ai_engine.model_status
        )

    def _simulate_triase(self, smiles: str) -> SimulationResponse:
        score = self.ai_engine.predict_dili_risk(smiles)
        
        risk_level = "low"
        if score > 0.66:
            risk_level = "high"
        elif score >= 0.33:
            risk_level = "medium"
            
        return SimulationResponse(
            mode="triase_umum",
            compound_name=None,
            input_smiles=smiles,
            dose_mg_kg=None,
            DILI_score=score,
            risk_level=risk_level,
            damage_severity=score, # Damage driven by AI score
            compound_class="unknown_general",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis.",
            disclaimer_permanent="Skor ini adalah estimasi awal berbasis model riset (AUC eksternal ~0,75-0,85), BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat.",
            disclaimer_hideable=False,
            affected_zone="Macro_Generic",
            supports_micro_zoom=False,
            explainability=self.ai_engine.get_explainability(smiles),
            visual_pattern="heatmap_generik",
            time_series_pkpd=None,
            nomogram_data=None,
            model_status=self.ai_engine.model_status
        )

    def _simulate_mock(self, req: SimulationRequest, dose: float) -> SimulationResponse:
        """Response dummy untuk pengembangan frontend (audit TA.8).
        TIDAK menyentuh pkpd_engine/ai_engine sama sekali — dipakai supaya
        endpoint tetap merespons walau konstanta PD kosong (assert_ready()
        TA.1 tetap utuh, tidak dilemahkan). Nilai dibuat mencolok (0.5, dst.)
        agar tidak mungkin disalahartikan sebagai hasil nyata. JANGAN aktifkan
        di produksi (lihat MOCK_MODE di app/core/config.py).
        """
        mode = req.mode
        is_edukasi = mode == "edukasi_mendalam"
        is_paracetamol = is_edukasi and req.compound_id == "paracetamol"

        mock_time_series = [{
            "time": 0.0, "concentration": 0.5, "c_liver": 0.5,
            "napqi": 0.5, "gsh": 0.5, "napqi_gsh_ratio": 0.5,
            "threshold_exceeded": False
        }] if is_paracetamol else None

        mock_nomogram = [{
            "time": 4, "plasma_concentration": 0.5,
            "rumack_line_150": 0.5, "rumack_line_200": 0.5
        }] if is_paracetamol else None

        if is_edukasi:
            compound_class = "dose_dependent" if is_paracetamol else "idiosyncratic"
            visual_pattern = "centrilobular_necrosis" if is_paracetamol else "portal_inflammation"
            affected_zone = "Zone_3" if is_paracetamol else "Portal_Periportal"
            disclaimer = (
                "[MOCK MODE] HepaTwin adalah alat bantu edukasi dan triase awal, "
                "BUKAN pengganti uji toksisitas atau keputusan klinis."
            )
        else:
            compound_class = "unknown_general"
            visual_pattern = "heatmap_generik"  # AGENTS.md §3.2: satu-satunya nilai sah untuk triase
            affected_zone = "Macro_Generic"
            disclaimer = (
                "[MOCK MODE] Skor ini adalah estimasi awal berbasis model riset "
                "(AUC eksternal ~0,75-0,85), BUKAN hasil uji toksisitas dan BUKAN "
                "dasar keputusan keamanan obat."
            )

        return SimulationResponse(
            mode=mode,
            compound_name="MOCK_COMPOUND" if is_edukasi else None,
            input_smiles=req.smiles_string if mode == "triase_umum" else None,
            dose_mg_kg=dose if is_edukasi else None,
            DILI_score=0.5,
            risk_level="medium",
            damage_severity=0.5,
            compound_class=compound_class,
            model_confidence_note="[MOCK MODE] Bukan hasil komputasi nyata — hanya untuk pengembangan frontend.",
            disclaimer_permanent=disclaimer,
            disclaimer_hideable=False if mode == "triase_umum" else True,
            affected_zone=affected_zone,
            supports_micro_zoom=is_edukasi,
            explainability=["MOCK_MODE_ACTIVE"],
            visual_pattern=visual_pattern,
            time_series_pkpd=mock_time_series,
            nomogram_data=mock_nomogram,
            model_status="mock"
        )