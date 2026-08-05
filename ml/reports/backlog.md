# backlog.md — Temuan di luar cakupan C1–C12 (Alur Kerja C)

Catatan sesuai `EXECUTION_PLAN_FIX_MODEL.md` Aturan Main #7 ("Jangan melebarkan
cakupan") — temuan yang muncul selama pengerjaan C1–C12 tapi bukan tanggung
jawab Alur C dicatat di sini, bukan diperbaiki langsung.

## 1. `segment_list` delimiter mismatch di `simulation_orchestrator.py`

**Ditemukan saat:** C2 (loader Supabase), lewat inspeksi data nyata.

**Fakta:** kolom `segment_list` di `hepatwin_compounds` berisi nilai yang
dipisah **titik koma**, mis. `"V;VI;VII;VIII"` (diverifikasi lewat query
langsung ke Supabase). Tapi `app/services/simulation_orchestrator.py` baris
92 melakukan:

```python
affected_segments = [s.strip() for s in compound.segment_list.split(",") if s.strip()]
```

— split pada **koma**, bukan titik koma. Untuk nilai `"V;VI;VII;VIII"`, ini
menghasilkan list satu elemen `["V;VI;VII;VIII"]`, bukan 4 elemen
`["V","VI","VII","VIII"]` seperti yang dimaksud.

**Dampak:** `SimulationResponse.affected_segments` (dikonsumsi frontend Alur E
untuk highlight segmen Couinaud 3D) kemungkinan salah untuk semua senyawa yang
py punya >1 segmen di `segment_list`.

**Kenapa tidak diperbaiki di sini:** `simulation_orchestrator.py` adalah milik
Alur F (fusi), PIC Faris — eksplisit di luar cakupan `PROJECT_FIX_MODEL.md` §6
("Mengubah logika autocomplete / `compound_repository.py` / `lookup_service.py`").
Meski file yang bug bukan persis salah satu dari ketiga nama itu, ia bagian
dari lapisan runtime yang sama (§5.1: "sudah benar untuk zona" — temuan ini
menunjukkan itu tidak sepenuhnya akurat untuk field `segment_list`).

**Rekomendasi:** ganti `.split(",")` → `.split(";")` di
`simulation_orchestrator.py` baris 92. Perbaikan satu baris, tidak menyentuh
logika lain.

## 2. `CompoundDetail` / `GET /compounds/{hepatwin_id}` mengakses kolom yang tidak ada di tabel nyata

**Ditemukan saat:** rekonstruksi `app/models/domain.py` (dampak dari file yang
hilang dari git, lihat commit terkait) — diperlukan untuk membuat `app/`
bisa di-import lagi ([KEPUTUSAN AI — dilakukan atas persetujuan eksplisit
pengguna], skema 42 kolom diverifikasi lewat `SELECT *` langsung ke Supabase).

**Fakta:** `app/api/endpoints/compounds.py` (`get_compound_detail`) mengakses
9 atribut pada objek `HepatwinCompound` yang **tidak ada** di skema tabel
`hepatwin_compounds` yang sebenarnya: `iupac_name`, `heavy_atom_count`,
`hydrogen_bond_donor_count`, `hydrogen_bond_acceptor_count`,
`rotatable_bond_count`, `exact_mass`, `monoisotopic_mass`, `charge`,
`complexity`. Field yang sama juga ada di `CompoundDetail` (`app/models/schemas.py`).

**Dampak:** `GET /compounds/{hepatwin_id}` akan **crash dengan
`AttributeError`** (500) untuk setiap request, karena `app/models/domain.py`
yang direkonstruksi hanya memetakan kolom yang benar-benar ada di tabel —
menambahkan 9 kolom karangan ke model akan membuat *setiap* query gagal
dengan `UndefinedColumn` dari Postgres, yang lebih buruk daripada
`AttributeError` pada satu endpoint.

**Kenapa tidak diperbaiki di sini:** `compounds.py` & `schemas.py`
(`CompoundDetail`) adalah bagian Alur B (autocomplete/lookup), bukan Alur
Kerja C. Kemungkinan 9 kolom ini direncanakan (deskriptor PubChem) tapi tidak
pernah benar-benar ditambahkan ke skema Supabase, atau dihapus setelah
`compounds.py` ditulis.

**Rekomendasi:** PIC Alur B/Faris perlu memutuskan salah satu: (a) tambah 9
kolom itu ke tabel Supabase kalau memang datanya ada di sumber PubChem asli,
atau (b) hapus 9 field itu dari `CompoundDetail` dan `get_compound_detail()`
kalau memang tidak pernah dipakai frontend.

**Status: DIPERBAIKI** (dengan izin eksplisit Ketua Tim/Faris via pengguna,
diverifikasi dulu tidak melanggar `HepaTwin_PRD.md` -- PRD tidak menyebut
satupun dari 9 field ini). Kedua opsi di atas dipilihkan opsi (b): 9 field
dihapus dari `CompoundDetail` (`app/models/schemas.py`) dan
`get_compound_detail()` (`app/api/endpoints/compounds.py`), karena field itu
tidak pernah punya sumber data nyata di Supabase sejak awal (bukan kolom yang
"hilang", tapi kolom yang tidak pernah ada). Faris tetap perlu meninjau
apakah field ini sebenarnya dibutuhkan frontend (opsi (a) masih terbuka bila
iya).

## 3. `compound_repository.py`: `get_compound_by_hepatwin_id` tidak menghormati dependency injection

**Ditemukan saat:** memperbaiki `tests/unit/test_api.py` (lihat #4) untuk
membuat `pytest tests/` hijau penuh.

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
