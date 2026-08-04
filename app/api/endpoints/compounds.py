from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.lookup_service import CompoundRepository
from app.models.schemas import AutocompleteResponse, CompoundItem, CompoundDetail

router = APIRouter()

@router.get("/compounds/autocomplete", response_model=AutocompleteResponse)
def autocomplete_compounds(
    q: str = Query(..., min_length=1, description="Kata kunci nama obat/senyawa INN"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    repo = CompoundRepository(db)
    results = repo.search_autocomplete(query=q, limit=limit)
    
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

@router.get("/compounds/{hepatwin_id}", response_model=CompoundDetail)
def get_compound_detail(
    hepatwin_id: str,
    db: Session = Depends(get_db)
):
    repo = CompoundRepository(db)
    item = repo.get_by_id(hepatwin_id)
    
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Senyawa dengan hepatwin_id '{hepatwin_id}' tidak ditemukan atau tidak mendukung simulasi (is_simulatable = FALSE)."
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
        injury_pattern=item.injury_pattern,
        segment_list=item.segment_list,
        hotspot_base_intensity=item.hotspot_base_intensity
    )
