from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.models.domain import HepatwinCompound
from cachetools import TTLCache
from cachetools.keys import hashkey
import threading
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

_search_cache = TTLCache(maxsize=2048, ttl=86400)
_search_lock = threading.Lock()

def _cached_search_ids(query: str, limit: int) -> List[str]:
    """
    TTLCache helper untuk ID autocomplete senyawa populer.
    Menggunakan double-checked locking untuk menghindari Cache Stampede (Thundering Herd).
    """
    key = hashkey(query, limit)
    try:
        return _search_cache[key]
    except KeyError:
        with _search_lock:
            if key in _search_cache:
                return _search_cache[key]
            
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
                result = list(db.scalars(stmt).all())
                _search_cache[key] = result
                return result
            except Exception as e:
                logger.error(f"Error pada LRU cache autocomplete: {e}")
                return []
            finally:
                db.close()

_get_compound_cache = TTLCache(maxsize=2048, ttl=86400)
_get_compound_lock = threading.Lock()

def _cached_get_compound(hepatwin_id: str) -> Optional[HepatwinCompound]:
    """
    TTLCache helper untuk mengambil detail senyawa secara penuh.
    Objek di-expunge dari session agar aman disimpan di memory.
    Menggunakan double-checked locking menghindari Cache Stampede.
    """
    key = hashkey(hepatwin_id)
    try:
        return _get_compound_cache[key]
    except KeyError:
        with _get_compound_lock:
            if key in _get_compound_cache:
                return _get_compound_cache[key]
                
            from app.core.database import SessionLocal
            db = SessionLocal()
            try:
                stmt = (
                    select(HepatwinCompound)
                    .where(HepatwinCompound.hepatwin_id == hepatwin_id.strip())
                    .where(HepatwinCompound.is_simulatable.is_(True))
                )
                compound = db.scalars(stmt).first()
                if compound:
                    db.expunge(compound)
                _get_compound_cache[key] = compound
                return compound
            except Exception as e:
                logger.error(f"Error pada TTLCache get compound: {e}")
                return None
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

        return _cached_get_compound(hepatwin_id)

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

