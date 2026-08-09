"""P3 -- Cache in-memory bounded LRU utk respons penuh POST /api/v1/simulate.

Mengapa: hasil simulasi DETERMINISTIK utk input tetap (senyawa + dosis +
kovariat) -- PRD menuntut keluaran 100% konsisten utk input identik. Kontes/
portal sering mensimulasikan senyawa yang sama berulang kali; cache
menghilangkan komputasi AI+SHAP+PBPK berulang di hot path.

Kunci cache = (hepatwin_id, dosis, kovariat, fingerprint data senyawa) --
BUKAN hepatwin_id saja: dosis & kovariat mengubah luaran PBPK (skala linier
dosis, penskalaan alometrik kovariat), dan fingerprint data senyawa (SMILES/
xlogp/injury_pattern/segment_list/hotspot) membuat cache kebal terhadap
perubahan data (atau mock test) dengan ID yang sama -- tidak pernah melayani
respons basi.

Footprint terukur: ~35-50 KB/entri (time-series PBPK 241 titik x 3 float +
shap_detail atoms). maxsize 512 -> ~20-25 MB worst-case, aman utk Hobby tier
FastAPI Cloud 512 MB (model GATNN-DNN hanya 3.5 MB di disk).

Invalidation: `clear_simulation_cache()` dipanggil dari
`CompoundRepository.clear_caches()` -- hook yang sama dgn reset registry
in-memory (P1), dipakai sesi test utk seed ulang DB.
"""
import threading

from cachetools import LRUCache

from app.models.domain import HepatwinCompound
from app.models.schemas import SimulationRequest, SimulationResponse

# 512 entri x ~20-25 KB = ~10-15 MB worst-case (lihat docstring modul).
_SIMULATION_CACHE_MAXSIZE = 512
_cache: LRUCache = LRUCache(maxsize=_SIMULATION_CACHE_MAXSIZE)
_lock = threading.Lock()
# Observabilitas produksi (via /health): hit/miss/store counters -- semua
# mutasi di bawah `_lock` yang sama, jadi snapshot konsisten dengan cache.
_stats = {"hits": 0, "misses": 0, "stores": 0}


def build_simulation_cache_key(request: SimulationRequest, compound: HepatwinCompound) -> tuple:
    """Kunci lengkap: input request + fingerprint data senyawa yang dipakai
    membentuk SimulationResponse. Dua request identik utk senyawa dgn data
    BEDA -> kunci BEDA (cache tidak pernah melayani data basi/mock utk ID
    yang sama)."""
    cov = request.covariates
    return (
        request.hepatwin_id,
        request.dosis_mg,
        cov.usia,
        cov.jenis_kelamin,
        cov.berat_badan_kg,
        cov.tinggi_badan_cm,
        compound.compound_name,
        compound.dili_concern,
        compound.canonical_smiles,
        compound.isomeric_smiles,
        compound.xlogp,
        compound.injury_pattern,
        compound.segment_list,
        compound.hotspot_base_intensity,
        compound.hotspot_display_mode,
    )


def get_simulation_cached(key: tuple) -> SimulationResponse | None:
    """Baca cache thread-safe; LRUCache sendiri tidak thread-safe, semua akses
    lewat lock ini. Menghitung hit/miss utk observabilitas /health."""
    with _lock:
        try:
            value = _cache[key]
            _stats["hits"] += 1
            return value
        except KeyError:
            _stats["misses"] += 1
            return None


def put_simulation_cached(key: tuple, response: SimulationResponse) -> None:
    """Simpan respons; LRU meng-evict entri terlama bila penuh."""
    with _lock:
        _cache[key] = response
        _stats["stores"] += 1


def clear_simulation_cache() -> None:
    """Buang seluruh entri -- dipanggil saat data senyawa berubah (seed ulang
    test) supaya tidak ada respons basi."""
    with _lock:
        _cache.clear()


def simulation_cache_size() -> int:
    with _lock:
        return len(_cache)


def simulation_cache_stats() -> dict:
    """Snapshot counters hit/miss + ukuran cache -- dipakai GET /health
    (observabilitas produksi: efektivitas cache P3 terpantau langsung dari
    endpoint live tanpa akses log). Hit-rate dihitung atas get (hit+miss),
    `stores` dilaporkan terpisah. Counter KUMULATIF seumur proses: tidak
    di-reset oleh `clear_simulation_cache()`/`CompoundRepository.clear_caches()`
    (yang hanya membuang entri, bukan riwayat) -- hit-rate = agregat lifetime."""
    with _lock:
        hits, misses, stores = _stats["hits"], _stats["misses"], _stats["stores"]
        size = len(_cache)
        maxsize = _cache.maxsize
    total = hits + misses
    return {
        "hits": hits,
        "misses": misses,
        "stores": stores,
        "hit_rate": round(hits / total, 4) if total else 0.0,
        "size": size,
        "maxsize": maxsize,
    }
