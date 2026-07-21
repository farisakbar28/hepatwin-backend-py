from fastapi import HTTPException
from app.models.schemas import SimulationRequest, SimulationResponse
from app.services.pkpd_engine import AcetaminophenPKPDEngine
from app.services.ai_engine import HybridAIEngine
from app.core.config import settings
import logging

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
                raise HTTPException(status_code=400, detail="compound_id harus 'paracetamol' atau 'amox_clav'")
            
            if compound_id == "paracetamol":
                return self._simulate_paracetamol(dose)
            elif compound_id == "amox_clav":
                return self._simulate_amox_clav(dose)
        
        else: # triase_umum
            if not smiles:
                raise HTTPException(status_code=400, detail="smiles_string wajib untuk mode triase_umum")
            
            if not self.ai_engine.validate_smiles(smiles):
                raise HTTPException(status_code=400, detail="smiles_string tidak valid")
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
            nomogram_data=nomogram
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
            nomogram_data=None
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
            nomogram_data=None
        )