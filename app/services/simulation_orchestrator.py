import logging
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.domain import HepatwinCompound
from app.services.lookup_service import CompoundRepository
from app.services.ai_engine import HybridAIEngine
from app.services.pbpk_engine import PBPKEngine
from app.services.exposure_evaluator import ExposureEvaluatorService
from app.services.fusion_service import FusionService
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
                detail=f"Senyawa dengan hepatwin_id '{request.hepatwin_id}' tidak ditemukan di database."
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
        # [KEPUTUSAN AI -- PENDING REVIEW KETUA TIM + FARIS, C10 gerbang G6]
        # get_shap_detail() (bukan get_explainability()) supaya shap_detail
        # tingkat atom (C8) bisa masuk SimulationResponse tanpa memanggil
        # explain() dua kali -- explainability_shap (List[str]) diturunkan
        # dari shap_detail["groups"] di bawah, satu sumber komputasi.
        shap_task = loop.run_in_executor(
            None,
            self.ai_engine.get_shap_detail,
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
        dili_score, shap_detail, (time_series_data, cmax_hati, auc_hati) = await asyncio.gather(
            ai_task, shap_task, pbpk_task
        )
        explainability_shap = [g["name"] for g in shap_detail["groups"]]

        # 3. LAPISAN FUSI RULE-BASED (Backend Fusi AI + PBPK + Lookup DB)
        # A. Evaluasi Tingkat Risiko, Warna WebGL, Kecepatan Kedip
        bmi = cov.berat_badan_kg / ((cov.tinggi_badan_cm/100)**2)
        
        exposure_result = ExposureEvaluatorService.evaluate_relative_exposure(
            cmax=cmax_hati,
            auc=auc_hati,
            age=cov.usia,
            bmi=bmi,
            dose_mg=request.dosis_mg,
            weight_kg=cov.berat_badan_kg
        )
        
        risk_level, visual_color, blinking_speed = FusionService.determine_visual_status(
            dili_score=dili_score,
            exposure_category=exposure_result["risk_level"]
        )

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
            disclaimer_permanent=disclaimer,
            shap_detail=shap_detail,
            model_version=self.ai_engine.model_version,
            model_status=self.ai_engine.model_status,
            score_is_calibrated=self.ai_engine.score_is_calibrated,
        )
