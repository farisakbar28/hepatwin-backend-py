from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.repositories.compound_registry import get_registry
from app.models.schemas import SimulationRequest
from app.models.domain import HepatwinCompound
import logging

logger = logging.getLogger(__name__)

async def verify_simulatable_compound(
    request: SimulationRequest,
    db: Session = Depends(get_db)
) -> None:
    """
    FastAPI Dependency (Pre-flight Validator) untuk memblokir request
    simulasi jika `hepatwin_id` merujuk ke senyawa biologik (is_simulatable = FALSE)
    atau ID tidak valid.
    """
    hepatwin_id = request.hepatwin_id.strip()
    
    # P1: lookup via registry in-memory (nol query DB di hot path); fallback
    # query DB bila registry belum dimuat (mis. TestClient tanpa startup).
    registry = get_registry()
    if registry is not None:
        compound = registry.get(hepatwin_id)
    else:
        # Kueri mentah untuk mendapatkan senyawa tanpa mempedulikan is_simulatable
        stmt = select(HepatwinCompound).where(HepatwinCompound.hepatwin_id == hepatwin_id)
        compound = db.scalars(stmt).first()

    if not compound:
        # Jika benar-benar tidak ada di database (ID fiktif)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Senyawa dengan hepatwin_id '{hepatwin_id}' tidak ditemukan di database."
        )

    if not compound.is_simulatable:
        # Jika senyawa ada tapi biologik (is_simulatable = FALSE)
        logger.warning(f"BLOCKED: Upaya simulasi untuk senyawa biologik {hepatwin_id} ({compound.compound_name})")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Senyawa ini bertipe biologik dan tidak dapat disimulasikan."
        )

    # Validasi SMILES
    smiles = compound.canonical_smiles or compound.isomeric_smiles
    if not smiles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Senyawa '{compound.compound_name}' tidak memiliki struktur SMILES yang valid untuk disimulasikan."
        )
