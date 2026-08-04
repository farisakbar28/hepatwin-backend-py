from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from app.models.domain import HepatwinCompound
from functools import lru_cache
from typing import List, Optional

# LRU Cache layer untuk autocomplete & lookup deterministik (TTL/limit 512 entries)

@lru_cache(maxsize=512)
def _cached_search_ids(query: str, limit: int) -> List[str]:
    """
    Cache pencarian ID senyawa berdasarkan kata kunci pencarian.
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
    finally:
        db.close()

class CompoundRepository:
    def __init__(self, db: Session):
        self.db = db

    def search_autocomplete(self, query: str, limit: int = 10) -> List[HepatwinCompound]:
        """
        Autocomplete pencarian senyawa.
        WAJIB memfilter `is_simulatable = TRUE`.
        Menggunakan in-memory caching untuk latensi <= 50ms.
        """
        if not query or not query.strip():
            return []

        # Ambil ID ter-cache
        target_ids = _cached_search_ids(query.strip().lower(), limit)
        if not target_ids:
            return []

        # Kueri ORM berdasarkan ID yang didapat dari cache
        stmt = (
            select(HepatwinCompound)
            .where(HepatwinCompound.hepatwin_id.in_(target_ids))
        )
        results = {c.hepatwin_id: c for c in self.db.scalars(stmt).all()}
        # Kembalikan sesuai urutan ID asli
        return [results[hid] for hid in target_ids if hid in results]

    def get_by_id(self, hepatwin_id: str) -> Optional[HepatwinCompound]:
        """
        Lookup detail senyawa by primary key `hepatwin_id`.
        Harus memfilter `is_simulatable = TRUE`.
        """
        stmt = (
            select(HepatwinCompound)
            .where(HepatwinCompound.hepatwin_id == hepatwin_id)
            .where(HepatwinCompound.is_simulatable.is_(True))
        )
        return self.db.scalars(stmt).first()
