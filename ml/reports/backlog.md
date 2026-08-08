# backlog.md — Temuan di luar cakupan C1–C12 (Alur Kerja C)

Catatan sesuai `EXECUTION_PLAN_FIX_MODEL.md` Aturan Main #7 ("Jangan melebarkan
cakupan") — temuan yang muncul selama pengerjaan C1–C12 tapi bukan tanggung
jawab Alur C dicatat di sini, bukan diperbaiki langsung.

## 1. `segment_list` delimiter mismatch (FIXED)

**Status: DIPERBAIKI.** `simulation_orchestrator.py` sudah menggunakan `.split(";")`.

## 2. `CompoundDetail` / `GET /compounds/{hepatwin_id}` mengakses kolom yang tidak ada di tabel nyata (FIXED)

**Status: DIPERBAIKI.** Field PubChem lama telah dihapus dari schema dan endpoint. FE mengikuti kontrak baru.

## 3. `compound_repository.py`: `get_compound_by_hepatwin_id` tidak menghormati dependency injection (TODO)

**Fakta:** `CompoundRepository.get_compound_by_hepatwin_id()` memanggil
`_cached_get_compound()`, yang membuat **`SessionLocal()` baru sendiri**
(`from app.core.database import SessionLocal` di dalam fungsi) alih-alih
memakai `self.db` yang di-inject lewat constructor `CompoundRepository(db)`.
Akibatnya: (a) test yang mem-mock `db` lewat constructor tidak pernah benar-benar
memengaruhi jalur ini -- mock diam-diam diabaikan, permintaan sungguhan
tetap jalan ke `SessionLocal()` asli; (b) hasil di-cache secara global
(`_get_compound_cache`, TTL 24 jam, keyed hanya oleh `hepatwin_id`) LINTAS
test/request apa pun dalam proses yang sama, termasuk lintas skenario test
yang seharusnya terisolasi.

**Dampak nyata:** `tests/unit/test_b5_integration.py::test_operational_error_handling`
gagal (`DID NOT RAISE OperationalError`) karena mock `side_effect` pada
`mock_db.scalars` tidak pernah tersentuh -- request sungguhan jalan duluan
(dari test lain di file yang sama yang kebetulan memakai `hepatwin_id` yang
sama, "HT-001") dan hasilnya (bukan exception) sudah ter-cache.

**Kenapa tidak diperbaiki di sini:** `compound_repository.py` eksplisit ada
di daftar terlarang `PROJECT_FIX_MODEL.md` §6 ("Mengubah logika autocomplete
/ `compound_repository.py` / `lookup_service.py`"). Perbaikan yang benar
(constructor injection dipakai konsisten, atau cache di-key dengan sesuatu
yang membedakan sumber DB) adalah keputusan desain PIC Alur B/D, bukan
tambalan satu baris yang aman diambil sepihak.

**Status: TIDAK diperbaiki**, `tests/unit/test_b5_integration.py::test_operational_error_handling`
tetap merah (1 dari 102 test backend) -- didokumentasikan di sini alih-alih
disembunyikan.

## 4. `tests/unit/test_api.py`: override dependency FastAPI di level modul (bukan fixture) meracuni seluruh sesi pytest

**Ditemukan saat:** menjalankan `pytest tests/` utuh untuk memverifikasi C0-C4
tidak meregresi -- 54 dari 102 test gagal padahal masing-masing file/modul
lulus bila dijalankan sendiri-sendiri.

**Fakta:** `tests/unit/test_api.py` baris 14 (sebelum perbaikan) adalah kode
**top-level** `app.dependency_overrides[get_db] = mock_get_db` -- dieksekusi
sekali saat modul di-*import* (fase collection pytest, SEBELUM test apa pun
benar-benar berjalan). Karena `app` adalah instance FastAPI singleton yang
sama dipakai seluruh sesi pytest, baris ini menimpa override
`app.dependency_overrides[get_db] = override_get_db` yang dipasang
`tests/conftest.py` (juga top-level, memakai SQLite in-memory berisi data
seed) -- **untuk sisa seluruh sesi**, termasuk test di `tests/e2e/` dan
`tests/security/` yang di-collect setelah `tests/unit/test_api.py`.
Akibatnya semua test itu memakai `MagicMock()` kosong sebagai sesi DB alih-alih
data seed SQLite, dan gagal massal.

**Status: DIPERBAIKI** (test-only, tidak menyentuh kode `app/`) --
diperbolehkan Ketua Tim/Faris karena murni isolasi test, tidak berkaitan
PRD. `app.dependency_overrides[get_db] = mock_get_db` dipindah ke fixture
`autouse=True` (`_override_get_db`) yang menyimpan & memulihkan nilai
sebelumnya setelah tiap test di modul ini -- override sekarang berlaku
per-test, bukan bocor ke seluruh sesi.

Verifikasi: `pytest tests/` -> 101 passed, 1 failed (item #3 di atas, di luar
cakupan Alur Kerja C) -- turun dari 54 failed sebelum perbaikan #2 dan #4.
