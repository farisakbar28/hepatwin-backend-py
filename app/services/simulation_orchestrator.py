import logging
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.domain import HepatwinCompound
from app.services.lookup_service import CompoundRepository
from app.services.ai_engine import HybridAIEngine
from app.services.pbpk_engine import PBPKEngine
from app.models.schemas import SimulationRequest, SimulationResponse, TimeSeriesPBPKPoint
from app.core.config import settings

logger = logging.getLogger(__name__)

class SimulationOrchestrator:
    def __init__(self):
        self.ai_engine = HybridAIEngine(model_path=settings.AI_MODEL_PATH)
        self.pbpk_engine = PBPKEngine()

    async def handle_simulation(self, request: SimulationRequest, db: Session) -> SimulationResponse:
        # 1. Lookup Senyawa di Database (OFFLINE & DETERMINISTIK)
        repo = CompoundRepository(db)
        compound = repo.get_by_id(request.hepatwin_id)
        
        if not compound:
            raise HTTPException(
                status_code=404,
                detail=f"Senyawa dengan hepatwin_id '{request.hepatwin_id}' tidak ditemukan atau tidak simulatable (is_simulatable = FALSE)."
            )

        smiles = compound.canonical_smiles or compound.isomeric_smiles
        if not smiles:
            raise HTTPException(
                status_code=400,
                detail=f"Senyawa '{compound.compound_name}' tidak memiliki struktur SMILES yang valid untuk disimulasikan."
            )

        # 2. EKSEKUSI PARALEL-ASINKRON (AI Predictor & PBPK Solver)
        # Menjalankan AI Inference & PBPK ODE Solver secara bersamaan via asyncio
        loop = asyncio.get_running_loop()

        # Task A: AI Predictor (PyTorch GATNN-DNN + SHAP)
        ai_task = loop.run_in_executor(
            None, 
            self.ai_engine.predict_dili_risk, 
            smiles
        )
        shap_task = loop.run_in_executor(
            None, 
            self.ai_engine.get_explainability, 
            smiles
        )

        # Task B: PBPK Solver (SciPy ODE + Alometrik)
        cov = request.covariates
        pbpk_task = loop.run_in_executor(
            None,
            self.pbpk_engine.simulate,
            request.dosis_mg,
            cov.usia,
            cov.jenis_kelamin,
            cov.berat_badan_kg,
            cov.tinggi_badan_cm
        )

        # Tunggu luaran kedua mesin secara asinkron
        dili_score, explainability_shap, (time_series_data, cmax_hati, auc_hati) = await asyncio.gather(
            ai_task, shap_task, pbpk_task
        )

        # 3. LAPISAN FUSI RULE-BASED (Backend Fusi AI + PBPK + Lookup DB)
        # A. Evaluasi Tingkat Risiko, Warna WebGL, Kecepatan Kedip
        risk_level = "low"
        visual_color = "green"
        blinking_speed = "none"

        if dili_score > 0.70 or (dili_score >= 0.50 and (cov.usia >= 60 or cov.berat_badan_kg / ((cov.tinggi_badan_cm/100)**2) >= 30)):
            risk_level = "high"
            visual_color = "red"
            blinking_speed = "fast"
        elif dili_score >= 0.30:
            risk_level = "medium"
            visual_color = "yellow"
            blinking_speed = "slow"

        # B. Pemetaan Segmen Couinaud dari Monograf LiverTox
        injury_pattern = compound.injury_pattern or "Fallback_Diffuse"
        affected_segments: List[str] = []

        if compound.segment_list:
            # Segment list disimpan sebagai koma terpisah, misal "V,VI,VII,VIII"
            affected_segments = [s.strip() for s in compound.segment_list.split(",") if s.strip()]
        else:
            # Fallback jika tidak ada monograf spesifik -> Difus seluruh segmen
            affected_segments = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]

        # C. Format Time Series Data
        ts_points = [
            TimeSeriesPBPKPoint(
                time=pt["time"],
                c_plasma=pt["c_plasma"],
                c_hati=pt["c_hati"]
            )
            for pt in time_series_data
        ]

        disclaimer = (
            "PENTING (MEDICAL DISCLAIMER): HepaTwin merupakan perangkat lunak penunjang keputusan (decision support system) "
            "praklinis murni in silico. Hasil prediksi dan visualisasi 3D bertujuan membantu penyusunan hipotesis ilmiah dan "
            "triase skrining awal, BUKAN diagnosis klinis, keputusan medis, atau pengganti mutlak bagi pengujian in vitro / in vivo. "
            "Seluruh kalkulasi beroperasi pada tingkat Context of Use berisiko rendah berdasarkan standar ASME V&V 40 (2018)."
        )

        return SimulationResponse(
            hepatwin_id=compound.hepatwin_id,
            compound_name=compound.compound_name,
            dili_score=round(float(dili_score), 4),
            risk_level=risk_level,
            visual_color=visual_color,
            blinking_speed=blinking_speed,
            affected_segments=affected_segments,
            injury_pattern=injury_pattern,
            explainability_shap=explainability_shap,
            cmax_hati=cmax_hati,
            auc_hati=auc_hati,
            time_series_pbpk=ts_points,
            disclaimer_permanent=disclaimer
        )
