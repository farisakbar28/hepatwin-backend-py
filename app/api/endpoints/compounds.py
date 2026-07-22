from fastapi import APIRouter

router = APIRouter()

# Senyawa flagship Mode Edukasi Mendalam (PRD §4.1). id sesuai nilai
# SimulationRequest.compound_id di app/models/schemas.py.
FLAGSHIP_COMPOUNDS = [
    {
        "id": "paracetamol",
        "display_name": "Paracetamol (Acetaminophen)",
        "mechanism_type": "dose_dependent",
        "supported_modes": ["edukasi_mendalam"],
    },
    {
        "id": "amox_clav",
        "display_name": "Amoxicillin-Clavulanate",
        "mechanism_type": "idiosyncratic",
        "supported_modes": ["edukasi_mendalam"],
    },
]


@router.get("/compounds")
def list_compounds() -> list[dict]:
    """Daftar senyawa flagship Mode Edukasi Mendalam (PRD §4.1)."""
    return FLAGSHIP_COMPOUNDS
