import logging
import time

from rdkit import Chem

from app.core.config import settings
from app.core.errors import (
    ModelUnavailableError,
    RequestIncompleteError,
    SmilesInvalidError,
)
from app.models.schemas import SimulationRequest, SimulationResponse
from app.services.explain import explain_compound
from app.services.pkpd_engine import AcetaminophenPKPDEngine
from app.services.predictor import get_backend

logger = logging.getLogger(__name__)

class SimulationOrchestrator:
    def __init__(self):
        self.pkpd_engine = AcetaminophenPKPDEngine()
        self.ai_backend = get_backend()

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

            try:
                mol = Chem.MolFromSmiles(smiles)
                valid = mol is not None
            except Exception:
                valid = False

            if not valid:
                raise SmilesInvalidError("smiles_string tidak valid")

            if settings.MOCK_MODE:
                return self._simulate_mock(req, dose)

            return self._simulate_triase(smiles)

    def _simulate_paracetamol(self, dose: float) -> SimulationResponse:
        # Mesin A (PK/PD) digembok sampai konstanta PD divalidasi Farmasi
        # (PRD §13 #1). Ubah gerbang RuntimeError/NotImplementedError menjadi error
        # typed yang jelas (503 E_MODEL_UNAVAILABLE) alih-alih 500 generik, supaya
        # frontend bisa menampilkan pesan yang benar. Ini TIDAK mengisi konstanta
        # atau melemahkan gerbang — hanya menyurfacekan keadaan tergembok dg rapi.
        try:
            time_series = self.pkpd_engine.simulate_napqi_gsh_dynamics(dose)
            nomogram = self.pkpd_engine.get_nomogram_data(dose)
        except (RuntimeError, NotImplementedError) as exc:
            logger.warning("Mesin A parasetamol belum siap: %s", exc)
            raise ModelUnavailableError(
                "Mode Edukasi parasetamol (Mesin A PK/PD) belum tersedia — konstanta "
                "farmakologi menunggu validasi anggota Farmasi (PRD §13 item #1)."
            ) from exc

        # Paracetamol SMILES untuk inference real
        apap_smiles = "CC(=O)NC1=CC=C(O)C=C1"
        mol = Chem.MolFromSmiles(apap_smiles)
        score = self.ai_backend.predict_proba(mol)
        
        risk_level = "low"
        if score > 0.66:
            risk_level = "high"
        elif score >= 0.33:
            risk_level = "medium"
            
        # Batasan model bersumber dari PRD §8.1 (Arsitektur §C.1)
        limitations = [
            "Model PK/PD menggunakan pendekatan satu-kompartemen (semula dua-kompartemen pada Morse et al. 2022).",
            "Volume distribusi menggunakan V1 (43,5 L/70kg) sebagai pendekatan Vd.",
            "Lag time absorpsi oral (5,3 menit) tidak dimasukkan ke dalam model.",
            "Parameter PK/PD hanya divalidasi untuk sukarelawan dewasa sehat.",
        ]
            
        return SimulationResponse(
            mode="edukasi_mendalam",
            compound_name="Paracetamol",
            input_smiles=None,
            dose_mg_kg=dose,
            DILI_score=score,
            risk_level=risk_level,
            damage_severity=min(1.0, dose / 150.0),
            compound_class="dose_dependent",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis.",
            disclaimer_permanent="HepaTwin adalah alat bantu edukasi dan triase awal, BUKAN pengganti uji toksisitas atau keputusan klinis.",
            disclaimer_hideable=True,
            affected_zone="Zone_3",
            supports_micro_zoom=True,
            explainability=explain_compound(mol),
            visual_pattern="centrilobular_necrosis",
            time_series_pkpd=time_series,
            nomogram_data=nomogram,
            model_status=self.ai_backend.model_status,
            model_limitations=limitations,
        )

    def _simulate_amox_clav(self, dose: float) -> SimulationResponse:
        # Use the correct Amoxicillin SMILES string for inference
        amox_smiles = "CC1(C)SC2C(NC(=O)C(N)c3ccc(O)cc3)C(=O)N12"
        mol = Chem.MolFromSmiles(amox_smiles)
        score = self.ai_backend.predict_proba(mol)
        
        risk_level = "low"
        if score > 0.66:
            risk_level = "high"
        elif score >= 0.33:
            risk_level = "medium"
            
        # Batasan model: amox-clav skor AI-driven (Arsitektur §B.2)
        limitations = [
            "Skor risiko dihasilkan oleh model AI tabular, bukan model PK/PD.",
            "Model dilatih pada dataset DILIrank dan divalidasi pada dataset Xu et al. (2015).",
            "Skor mencerminkan probabilitas DILI concern berdasarkan struktur kimia, bukan mekanisme spesifik.",
        ]
            
        return SimulationResponse(
            mode="edukasi_mendalam",
            compound_name="Amoxicillin-Clavulanate",
            input_smiles=None,
            dose_mg_kg=dose,
            DILI_score=score,
            risk_level=risk_level,
            damage_severity=score,
            compound_class="idiosyncratic",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis.",
            disclaimer_permanent="HepaTwin adalah alat bantu edukasi dan triase awal, BUKAN pengganti uji toksisitas atau keputusan klinis.",
            disclaimer_hideable=True,
            affected_zone="Portal_Periportal",
            supports_micro_zoom=True,
            explainability=explain_compound(mol),
            visual_pattern="portal_inflammation",
            time_series_pkpd=None,
            nomogram_data=None,
            model_status=self.ai_backend.model_status,
            model_limitations=limitations,
        )

    def _simulate_triase(self, smiles: str) -> SimulationResponse:
        # Timing untuk optimasi NFR PRD §6 (< 5 detik mode triase)
        t0 = time.perf_counter()
        
        mol = Chem.MolFromSmiles(smiles)
        t_parse = time.perf_counter()
        
        score = self.ai_backend.predict_proba(mol)
        t_predict = time.perf_counter()
        
        expl = explain_compound(mol)
        t_explain = time.perf_counter()
        
        logger.info(
            "Triase timing: parse=%.3fms predict=%.3fms explain=%.3fms total=%.3fms",
            (t_parse - t0) * 1000,
            (t_predict - t_parse) * 1000,
            (t_explain - t_predict) * 1000,
            (t_explain - t0) * 1000,
        )
        
        risk_level = "low"
        if score > 0.66:
            risk_level = "high"
        elif score >= 0.33:
            risk_level = "medium"
            
        # Batasan model untuk mode triase (Arsitektur §E.3)
        limitations = [
            "Skor berbasis model riset yang dilatih pada dataset obat terbatas, bukan hasil uji klinis.",
            "Mode triase tidak menentukan pola mekanisme spesifik (hepatoselular vs kolestatik).",
            "Heatmap yang ditampilkan bersifat generik dan bukan representasi histologis sebenarnya.",
        ]
            
        return SimulationResponse(
            mode="triase_umum",
            compound_name=None,
            input_smiles=smiles,
            dose_mg_kg=None,
            DILI_score=score,
            risk_level=risk_level,
            damage_severity=score,
            compound_class="unknown_general",
            model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis.",
            disclaimer_permanent="Skor ini adalah estimasi awal berbasis model riset (AUC eksternal ~0,75-0,85), BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat.",
            disclaimer_hideable=False,
            affected_zone="Macro_Generic",
            supports_micro_zoom=False,
            explainability=expl,
            visual_pattern="heatmap_generik",
            time_series_pkpd=None,
            nomogram_data=None,
            model_status=self.ai_backend.model_status,
            model_limitations=limitations,
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