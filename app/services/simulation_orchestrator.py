import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.domain import HepatwinCompound
from app.services.lookup_service import CompoundRepository
from app.services.ai_engine import HybridAIEngine
from app.services.pbpk_engine import PBPKEngine
from app.services.exposure_evaluator import ExposureEvaluatorService
from app.services.fusion_service import FusionService
from app.models.schemas import SimulationRequest, SimulationResponse, TimeSeriesPBPKPoint, FusionThresholds
from app.core.config import settings

logger = logging.getLogger(__name__)


# R7 (gerbang G5, PRD v2.3 SS8.3.3): label siap-tampil -- "Aman/Berbahaya/
# Kritis" tidak boleh berdiri sendiri. risk_level (low/medium/high) TIDAK
# berubah, tetap enum teknis utk logika/frontend lama.
RISK_LABEL_ID = {
    "low": "Prioritas rendah (in-silico)",
    "medium": "Prioritas sedang (in-silico)",
    "high": "Prioritas tinggi (in-silico)",
}
RISK_LABEL_DISCLAIMER = (
    "Warna dan label menunjukkan prioritas kajian in-silico, bukan keputusan terapi maupun klaim "
    "keamanan klinis."
)

# R6 (gerbang G3): proksi mapping_confidence dari livertox_match_method --
# kolom mapping_confidence yang diminta PRD v2.3 SS8.3.1 belum ada di DB.
MAPPING_CONFIDENCE_PROXY = {
    "exact_name": "high",
    "salt_ester_normalized": "medium",
    "leading_salt_normalized": "medium",
    "spelling_variant_normalized": "medium",
    "no_match": "none",
}


def _timed(fn, *args):
    """F6 (D7): jalankan `fn(*args)` di thread executor, ukur durasinya
    sendiri (bukan dari sisi caller) -- caller hanya melihat waktu
    `await`, bukan waktu eksekusi murni di thread pekerja."""
    start = time.perf_counter()
    result = fn(*args)
    return result, time.perf_counter() - start


class SimulationOrchestrator:
    def __init__(self):
        self.ai_engine = HybridAIEngine(model_path=settings.AI_MODEL_PATH)
        self.pbpk_engine = PBPKEngine()

    async def handle_simulation(
        self, request: SimulationRequest, db: Session,
        timing_sink: Optional[Dict[str, float]] = None,
    ) -> SimulationResponse:
        """
        `timing_sink` (F6, D7): dict opsional yang diisi durasi per-tahap
        (ms) bila disediakan pemanggil -- dipakai skrip benchmark/test, TIDAK
        pernah otomatis masuk response body (lihat F7 utk `timing_ms`
        tergerbang `settings.DEBUG`). Selalu di-log server-side lewat
        `logger.info` terlepas dari `timing_sink`.
        """
        t_start = time.perf_counter()

        # 1. Lookup Senyawa di Database (OFFLINE & DETERMINISTIK)
        repo = CompoundRepository(db)
        compound = repo.get_by_id(request.hepatwin_id)
        t_lookup_done = time.perf_counter()

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
            _timed,
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
            _timed,
            self.ai_engine.get_shap_detail,
            smiles
        )

        # Task B: PBPK Solver (SciPy ODE + Alometrik, v2.3)
        cov = request.covariates
        pbpk_task = loop.run_in_executor(
            None,
            _timed,
            self.pbpk_engine.simulate_with_diagnostics,
            request.dosis_mg,
            cov.usia,
            cov.jenis_kelamin,
            cov.berat_badan_kg,
            cov.tinggi_badan_cm,
            compound.xlogp,
        )

        # Tunggu luaran ketiga tugas secara asinkron
        t_parallel_start = time.perf_counter()
        (dili_score, t_ai), (shap_detail, t_shap), (pbpk_result, t_pbpk) = await asyncio.gather(
            ai_task, shap_task, pbpk_task
        )
        t_parallel_wall = time.perf_counter() - t_parallel_start
        explainability_shap = [g["name"] for g in shap_detail["groups"]]

        # 3. LAPISAN FUSI RULE-BASED (Backend Fusi AI + PBPK + Lookup DB)
        # A. Evaluasi Tingkat Risiko, Warna WebGL, Kecepatan Kedip
        t_exposure_start = time.perf_counter()
        exposure_result = ExposureEvaluatorService.evaluate_relative_exposure(
            cmax=pbpk_result.cmax_hati,
            auc=pbpk_result.auc_hati,
        )
        t_exposure = time.perf_counter() - t_exposure_start

        t_fusion_start = time.perf_counter()
        fusion_result = FusionService.determine_visual_status(
            dili_score=dili_score,
            exposure_category=exposure_result["risk_level"]
        )
        t_fusion = time.perf_counter() - t_fusion_start
        risk_level, visual_color, blinking_speed = (
            fusion_result.risk_level, fusion_result.visual_color, fusion_result.blinking_speed
        )

        # B. Pemetaan Segmen Couinaud dari Monograf LiverTox
        injury_pattern = compound.injury_pattern or "Fallback_Diffuse"
        affected_segments: List[str] = []

        if compound.segment_list:
            # Segment list disimpan dengan pemisah titik-koma di DB nyata, mis.
            # "V;VI;VII;VIII" (BUKAN koma -- diverifikasi lewat query langsung
            # ke seluruh 1.231 senyawa is_simulatable=TRUE, F4). split(",") versi
            # lama tidak pernah menemukan pemisah pada data nyata, sehingga
            # affected_segments selalu berisi satu string gabungan yang salah
            # utk 100% senyawa -- ditemukan & diperbaiki di sini (F4).
            affected_segments = [s.strip() for s in compound.segment_list.split(";") if s.strip()]
        else:
            # Fallback jika tidak ada monograf spesifik -> Difus seluruh segmen
            affected_segments = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]

        # C. Intensitas & mode hotspot (F4, PROJECT_FUSION.md SS4.3) -- lookup DB
        # murni ("di mana, dan seberapa kuat buktinya"), TIDAK memengaruhi
        # warna/kedip (itu murni hasil fusion_result di atas, "seberapa berisiko").
        is_evidence_fallback = injury_pattern == "Tidak Terklasifikasi" or not compound.segment_list
        hotspot_intensity = compound.hotspot_base_intensity or "dim"
        hotspot_display_mode = compound.hotspot_display_mode or "diffuse"
        evidence_note = (
            "Pola cedera spesifik untuk senyawa ini belum tersedia di data kurasi; "
            "hotspot ditampilkan difus redup sebagai default aman."
            if is_evidence_fallback else None
        )

        # C2. Sinyal eskalasi PRD v2.3 SS8.3.3 (R5, gerbang G1/G2) -- INFORMATIF
        # SAJA, tidak memengaruhi warna. Lihat reports/R4_dampak_eskalasi.md.
        metabolic_risk_flag = bool(pbpk_result.parameters.get("metabolic_risk_flag", False))
        metabolic_risk_note = (
            "Pasien memiliki BMI >= 30 (indikator risiko metabolik/MASLD). Catatan informatif -- "
            "BELUM memengaruhi warna/prioritas visual, menunggu keputusan Farmasi (gerbang G1)."
            if metabolic_risk_flag else None
        )
        evidence_strength = "specific" if injury_pattern in {"Hepatoseluler", "Kolestatik", "Campuran"} else "none"
        evidence_strength_note = (
            "Senyawa ini memiliki pola cedera spesifik di monograf LiverTox. Catatan informatif -- "
            "BELUM memengaruhi warna/prioritas visual menjadi MERAH otomatis, menunggu definisi "
            "'strong evidence' dari Farmasi (gerbang G2)."
            if evidence_strength == "specific" else None
        )

        # C3. livertox_match_method + proksi mapping_confidence (R6, gerbang G3)
        livertox_match_method = compound.livertox_match_method
        mapping_confidence = MAPPING_CONFIDENCE_PROXY.get(livertox_match_method, "none")

        # D. Format Time Series Data
        ts_points = [
            TimeSeriesPBPKPoint(
                time=pt["time"],
                c_plasma=pt["c_plasma"],
                c_hati=pt["c_hati"]
            )
            for pt in pbpk_result.time_series
        ]

        disclaimer = (
            "PENTING (MEDICAL DISCLAIMER): HepaTwin merupakan perangkat lunak penunjang keputusan (decision support system) "
            "praklinis murni in silico. Hasil prediksi dan visualisasi 3D bertujuan membantu penyusunan hipotesis ilmiah dan "
            "triase skrining awal, BUKAN diagnosis klinis, keputusan medis, atau pengganti mutlak bagi pengujian in vitro / in vivo. "
            "Model PBPK Fase 1 adalah model linear bolus tunggal tanpa absorpsi oral, protein binding, Km/Vmax, "
            "NAPQI/glutathione depletion, atau parameter IVIVE compound-specific penuh. Ambang exposure bersifat "
            "kalibrasi distribusional internal, bukan ambang klinis."
        )

        # E. Instrumentasi latensi per-tahap (F6, D7) -- server-side saja,
        # TIDAK pernah otomatis masuk response body (lihat F7 utk timing_ms
        # tergerbang settings.DEBUG).
        t_total = time.perf_counter() - t_start
        timing_ms = {
            "lookup_ms": round((t_lookup_done - t_start) * 1000, 2),
            "ai_inference_ms": round(t_ai * 1000, 2),
            "shap_ms": round(t_shap * 1000, 2),
            "pbpk_ms": round(t_pbpk * 1000, 2),
            "parallel_wall_ms": round(t_parallel_wall * 1000, 2),
            "exposure_eval_ms": round(t_exposure * 1000, 2),
            "fusion_ms": round(t_fusion * 1000, 2),
            "total_ms": round(t_total * 1000, 2),
        }
        logger.info("F6 timing hepatwin_id=%s: %s", compound.hepatwin_id, timing_ms)
        if timing_sink is not None:
            timing_sink.update(timing_ms)

        return SimulationResponse(
            hepatwin_id=compound.hepatwin_id,
            compound_name=compound.compound_name,
            dili_score=round(float(dili_score), 4),
            risk_level=risk_level,
            risk_label_id=RISK_LABEL_ID[risk_level],
            risk_label_disclaimer=RISK_LABEL_DISCLAIMER,
            visual_color=visual_color,
            blinking_speed=blinking_speed,
            affected_segments=affected_segments,
            injury_pattern=injury_pattern,
            segment_mapping_type="PEDAGOGICAL_HEURISTIC",
            segment_mapping_not_clinical_localization=True,
            hotspot_intensity=hotspot_intensity,
            hotspot_display_mode=hotspot_display_mode,
            evidence_note=evidence_note,
            explainability_shap=explainability_shap,
            cmax_hati=pbpk_result.cmax_hati,
            auc_hati=pbpk_result.auc_hati,
            cmax_auc_ratio=exposure_result["cmax_auc_ratio"],
            shape_ratio_h_inv=exposure_result["shape_ratio_h_inv"],
            exposure_index=exposure_result["exposure_index"],
            exposure_category=exposure_result["risk_level"],
            exposure_category_source=exposure_result["exposure_category_source"],
            exposure_calibration_version=exposure_result["calibration_version"],
            metabolic_risk_flag=metabolic_risk_flag,
            metabolic_risk_note=metabolic_risk_note,
            evidence_strength=evidence_strength,
            evidence_strength_note=evidence_strength_note,
            livertox_match_method=livertox_match_method,
            mapping_confidence=mapping_confidence,
            time_series_pbpk=ts_points,
            disclaimer_permanent=disclaimer,
            shap_detail=shap_detail,
            model_version=self.ai_engine.model_version,
            model_status=self.ai_engine.model_status,
            score_is_calibrated=self.ai_engine.score_is_calibrated,
            fusion_reason=fusion_result.fusion_reason,
            thresholds_used=FusionThresholds(t_low=settings.FUSION_AI_T_LOW, t_high=settings.FUSION_AI_T_HIGH),
            timing_ms=timing_ms if settings.DEBUG else None,
        )
