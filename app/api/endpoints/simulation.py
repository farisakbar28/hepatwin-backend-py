from fastapi import APIRouter, HTTPException
from app.models.schemas import SimulationRequest, SimulationResponse

router = APIRouter()

@router.post("/simulate", response_model=SimulationResponse)
def simulate_dili(request: SimulationRequest):
    if request.mode == "edukasi_mendalam":
        if request.compound_id == "paracetamol":
            return SimulationResponse(
                mode=request.mode,
                compound_name="Paracetamol",
                DILI_score=0.85,
                model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis",
                affected_zone="Zone_3",
                explainability=["Phenol group", "Acetamide group"],
                visual_pattern="sentrilobuler",
                time_series_pkpd=[
                    {"time": 0, "NAPQI_ratio": 0.1},
                    {"time": 4, "NAPQI_ratio": 0.5},
                    {"time": 8, "NAPQI_ratio": 0.9}
                ]
            )
        elif request.compound_id == "amox_clav":
            return SimulationResponse(
                mode=request.mode,
                compound_name="Amoxicillin-Clavulanate",
                DILI_score=0.72,
                model_confidence_note="Estimasi awal berbasis model riset, bukan hasil uji klinis",
                affected_zone="Portal_Periportal",
                explainability=["Beta-lactam ring"],
                visual_pattern="portal_periportal",
                time_series_pkpd=None
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid compound_id for edukasi_mendalam")

    elif request.mode == "triase_umum":
        if not request.smiles_string:
            raise HTTPException(status_code=400, detail="smiles_string required for triase_umum")
        return SimulationResponse(
            mode=request.mode,
            input_smiles=request.smiles_string,
            DILI_score=0.58,
            model_confidence_note="Skor ini adalah estimasi awal berbasis model riset (AUC eksternal ~0.75-0.85), BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat.",
            affected_zone=None,
            explainability=["Gugus toksik reaktif (mock)"],
            visual_pattern="heatmap_generik",
            time_series_pkpd=None
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")