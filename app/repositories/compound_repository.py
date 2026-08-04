from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.models.domain import HepatwinCompound
from functools import lru_cache
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=512)
def _cached_search_ids(query: str, limit: int) -> List[str]:
    """
    LRU Cache helper untuk ID autocomplete senyawa populer.
    Menggunakan SessionLocal independen tanpa menahan koneksi terbuka.
    """
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        clean_query = query.strip().lower()
        stmt = (
            select(HepatwinCompound.hepatwin_id)
            .where(HepatwinCompound.is_simulatable.is_(True))
            .where(
                or_(
                    func.lower(HepatwinCompound.compound_name).like(f"{clean_query}%"),
                    func.lower(HepatwinCompound.compound_name_normalized).like(f"{clean_query}%"),
                    func.lower(HepatwinCompound.compound_name).like(f"%{clean_query}%")
                )
            )
            .order_by(
                func.lower(HepatwinCompound.compound_name).like(f"{clean_query}%").desc(),
                HepatwinCompound.compound_name.asc()
            )
            .limit(limit)
        )
        return list(db.scalars(stmt).all())
    except Exception as e:
        logger.error(f"Error pada LRU cache autocomplete: {e}")
        return []
    finally:
        db.close()

class CompoundRepository:
    """
    Data Access Object (DAO) / Repository untuk tabel `public.hepatwin_compounds`.
    Menangani lookup deterministik by ID dan autocomplete pencarian nama senyawa.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_compound_by_hepatwin_id(self, hepatwin_id: str) -> Optional[HepatwinCompound]:
        """
        Lookup detail senyawa berdasarkan `hepatwin_id`.
        WAJIB memfilter `is_simulatable = TRUE`. 
        Menyingkirkan 105 senyawa biologik (is_simulatable = FALSE).
        """
        if not hepatwin_id or not hepatwin_id.strip():
            return None

        stmt = (
            select(HepatwinCompound)
            .where(HepatwinCompound.hepatwin_id == hepatwin_id.strip())
            .where(HepatwinCompound.is_simulatable.is_(True))
        )
        return self.db.scalars(stmt).first()

    def search_by_name(self, query: str, limit: int = 10) -> List[HepatwinCompound]:
        """
        Pencarian autocomplete senyawa berdasarkan nama obat (INN/Normalized).
        WAJIB memfilter `is_simulatable = TRUE`.
        Menggunakan caching in-memory via `_cached_search_ids` untuk latensi <= 50ms.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip().lower()
        target_ids = _cached_search_ids(clean_query, limit)
        
        if not target_ids:
            # Fallback jika LRU cache kosong / bypass
            stmt = (
                select(HepatwinCompound)
                .where(HepatwinCompound.is_simulatable.is_(True))
                .where(
                    or_(
                        func.lower(HepatwinCompound.compound_name).like(f"{clean_query}%"),
                        func.lower(HepatwinCompound.compound_name_normalized).like(f"{clean_query}%"),
                        func.lower(HepatwinCompound.compound_name).like(f"%{clean_query}%")
                    )
                )
                .order_by(
                    func.lower(HepatwinCompound.compound_name).like(f"{clean_query}%").desc(),
                    HepatwinCompound.compound_name.asc()
                )
                .limit(limit)
            )
            return list(self.db.scalars(stmt).all())

        stmt = (
            select(HepatwinCompound)
            .where(HepatwinCompound.hepatwin_id.in_(target_ids))
        )
        results = {c.hepatwin_id: c for c in self.db.scalars(stmt).all()}
        return [results[hid] for hid in target_ids if hid in results]

    # Alias untuk kompatibilitas mundur dengan test suite eksisting
    get_by_id = get_compound_by_hepatwin_id
    search_autocomplete = search_by_name

