from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.core.database import get_db
from app.repositories.compound_repository import CompoundRepository
from app.models.schemas import AutocompleteResponse, CompoundItem, CompoundDetail
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/compounds/autocomplete", response_model=AutocompleteResponse)
def autocomplete_compounds(
    q: str = Query(..., min_length=1, description="Kata kunci nama obat/senyawa INN"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter pencarian 'q' tidak boleh kosong."
        )

    try:
        repo = CompoundRepository(db)
        results = repo.search_by_name(query=q, limit=limit)
        
        items = [
            CompoundItem(
                hepatwin_id=item.hepatwin_id,
                compound_name=item.compound_name,
                dili_concern=item.dili_concern,
                is_simulatable=item.is_simulatable
            )
            for item in results
        ]
        return AutocompleteResponse(query=q, total=len(items), results=items)
    except OperationalError as e:
        logger.error(f"Database OperationalError saat autocomplete: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database Supabase terputus atau tidak dapat dihubungi. Silakan coba beberapa saat lagi."
        )
    except SQLAlchemyError as e:
        logger.error(f"Database SQLAlchemyError saat autocomplete: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan internal pada layanan kueri database."
        )

@router.get("/compounds/{hepatwin_id}", response_model=CompoundDetail)
def get_compound_detail(
    hepatwin_id: str,
    db: Session = Depends(get_db)
):
    if not hepatwin_id or not hepatwin_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter 'hepatwin_id' tidak valid."
        )

    try:
        repo = CompoundRepository(db)
        item = repo.get_compound_by_hepatwin_id(hepatwin_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Senyawa dengan hepatwin_id '{hepatwin_id}' tidak ditemukan atau tidak tersedia untuk simulasi 3D (is_simulatable = FALSE)."
            )
            
        return CompoundDetail(
            hepatwin_id=item.hepatwin_id,
            compound_name=item.compound_name,
            dili_concern=item.dili_concern,
            is_simulatable=item.is_simulatable,
            ltkb_id=item.ltkb_id,
            cid=item.cid,
            canonical_smiles=item.canonical_smiles,
            isomeric_smiles=item.isomeric_smiles,
            inchikey=item.inchikey,
            molecular_formula=item.molecular_formula,
            molecular_weight=item.molecular_weight,
            tpsa=item.tpsa,
            xlogp=item.xlogp,
            iupac_name=item.iupac_name,
            heavy_atom_count=item.heavy_atom_count,
            hydrogen_bond_donor_count=item.hydrogen_bond_donor_count,
            hydrogen_bond_acceptor_count=item.hydrogen_bond_acceptor_count,
            rotatable_bond_count=item.rotatable_bond_count,
            exact_mass=item.exact_mass,
            monoisotopic_mass=item.monoisotopic_mass,
            charge=item.charge,
            complexity=item.complexity,
            injury_pattern=item.injury_pattern,
            segment_list=item.segment_list,
            hotspot_base_intensity=item.hotspot_base_intensity
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database OperationalError saat detail lookup: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database Supabase terputus atau tidak dapat dihubungi. Silakan coba beberapa saat lagi."
        )
    except SQLAlchemyError as e:
        logger.error(f"Database SQLAlchemyError saat detail lookup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan internal pada layanan kueri database."
        )

