from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.models.domain import HepatwinCompound
from app.repositories.compound_registry import get_registry, reset_registry
from cachetools import TTLCache
from cachetools.keys import hashkey
import threading
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

_search_cache = TTLCache(maxsize=2048, ttl=86400)
_search_lock = threading.Lock()

_get_compound_cache = TTLCache(maxsize=2048, ttl=86400)
_get_compound_lock = threading.Lock()

def clear_caches():
    # P1: registry in-memory ikut di-reset supaya test mendapat state bersih.
    reset_registry()
    # P3: respons /simulate yang di-cache ikut dibuang -- dipanggil saat data
    # senyawa berubah (seed ulang DB di sesi test), cegah respons basi.
    from app.services.simulation_cache import clear_simulation_cache
    clear_simulation_cache()
    with _search_lock:
        _search_cache.clear()
    with _get_compound_lock:
        _get_compound_cache.clear()

class CompoundRepository:
    """
    Data Access Object (DAO) / Repository untuk tabel `public.hepatwin_compounds`.
    Menangani lookup deterministik by ID dan autocomplete pencarian nama senyawa.
    """
    def __init__(self, db: Session):
        self.db = db

    def _is_mock_db(self) -> bool:
        return "Mock" in type(self.db).__name__

    def get_compound_by_hepatwin_id(self, hepatwin_id: str) -> Optional[HepatwinCompound]:
        """
        Lookup detail senyawa berdasarkan `hepatwin_id`.
        WAJIB memfilter `is_simulatable = TRUE`. 
        Menyingkirkan 105 senyawa biologik (is_simulatable = FALSE).
        """
        if not hepatwin_id or not hepatwin_id.strip():
            return None

        clean_id = hepatwin_id.strip()
        is_mock = self._is_mock_db()

        # P1: jalur cepat in-memory (registry dimuat saat startup) -- nol query
        # DB di hot path. Registry menyimpan SEMUA baris (termasuk biologik),
        # jadi filter is_simulatable diterapkan di sini, persis query SQL lama.
        # Mock db (unit test) sengaja dilewati supaya jalur error-handling DB
        # lama tetap teruji -- fast-path hanya untuk session DB nyata.
        if not is_mock:
            registry = get_registry()
            if registry is not None:
                compound = registry.get(clean_id)
                if compound is None:
                    return None
                return compound if compound.is_simulatable else None

        key = hashkey(clean_id)
        
        if not is_mock:
            try:
                return _get_compound_cache[key]
            except KeyError:
                pass

        with _get_compound_lock:
            if not is_mock and key in _get_compound_cache:
                return _get_compound_cache[key]
            
            for attempt in range(2):
                try:
                    stmt = (
                        select(HepatwinCompound)
                        .where(HepatwinCompound.hepatwin_id == clean_id)
                        .where(HepatwinCompound.is_simulatable.is_(True))
                    )
                    compound = self.db.scalars(stmt).first()
                    if compound and not is_mock:
                        try:
                            self.db.expunge(compound)
                        except Exception:
                            pass
                        _get_compound_cache[key] = compound
                    return compound
                except (OperationalError, SQLAlchemyError) as e:
                    logger.error(f"Error DB pada get compound (attempt {attempt+1}): {e}")
                    try:
                        self.db.rollback()
                    except Exception:
                        pass
                    if attempt == 1:
                        raise e
                except Exception as e:
                    logger.error(f"Error non-DB pada get compound: {e}")
                    raise e
            return None

    def search_by_name(self, query: str, limit: int = 10) -> List[HepatwinCompound]:
        """
        Pencarian autocomplete senyawa berdasarkan nama obat (INN/Normalized).
        WAJIB memfilter `is_simulatable = TRUE`.
        Menggunakan caching in-memory via TTLCache untuk latensi <= 50ms.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip().lower()
        is_mock = self._is_mock_db()

        # P1: jalur cepat in-memory -- replikasi deterministik query SQL lama
        # (prefix/substring, filter is_simulatable, ordering) tanpa I/O DB.
        # Mock db dilewati (lihat get_compound_by_hepatwin_id).
        if not is_mock:
            registry = get_registry()
            if registry is not None:
                return registry.search(query, limit=limit)

        key = hashkey(clean_query, limit)
        
        if not is_mock:
            try:
                return _search_cache[key]
            except KeyError:
                pass

        with _search_lock:
            if not is_mock and key in _search_cache:
                return _search_cache[key]
            
            for attempt in range(2):
                try:
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
                    results = list(self.db.scalars(stmt).all())
                    if results and not is_mock:
                        for c in results:
                            try:
                                self.db.expunge(c)
                            except Exception:
                                pass
                        _search_cache[key] = results
                    return results
                except (OperationalError, SQLAlchemyError) as e:
                    logger.error(f"Error DB pada search_by_name (attempt {attempt+1}): {e}")
                    try:
                        self.db.rollback()
                    except Exception:
                        pass
                    if attempt == 1:
                        raise e
                except Exception as e:
                    logger.error(f"Error non-DB pada search_by_name: {e}")
                    raise e
            return []

    def get_all_simulatable(self) -> List[HepatwinCompound]:
        """Ambil SELURUH senyawa `is_simulatable = TRUE` (tanpa limit, tanpa
        cache TTL). Dipakai skrip diagnostik batch (mis. F1
        `scripts/diagnose_score_distribution.py`), BUKAN jalur request HTTP --
        beda dari `get_compound_by_hepatwin_id`/`search_by_name` yang dioptimasi
        untuk lookup satuan bertahan-cepat.
        """
        stmt = select(HepatwinCompound).where(HepatwinCompound.is_simulatable.is_(True))
        compounds = list(self.db.scalars(stmt).all())
        for c in compounds:
            try:
                self.db.expunge(c)
            except Exception:
                pass
        return compounds

    # Alias untuk kompatibilitas mundur dengan test suite eksisting
    get_by_id = get_compound_by_hepatwin_id
    search_autocomplete = search_by_name
