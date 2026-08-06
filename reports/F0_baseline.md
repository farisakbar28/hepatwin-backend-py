# F0 — Baseline Branch `fusion` (D7 & D9)

**Snapshot:** 2026-08-06T02:50:52Z (UTC)
**Branch:** `fusion` (bercabang dari `master`, commit `e0e7e77` — merge `fix-model`)
**Python:** 3.10.11 (`.venv`)

---

## 1. Status branch

Branch `fusion` sudah ada sebelumnya (tracking `origin/fusion`, up to date). `PROJECT_FUSION.md` dan
`EXECUTION_PLAN_FUSION.md` sudah berada di root repo (untracked sebelum commit F0 ini). Dua dokumen lama
`PROJECT_FIX_MODEL.md` / `EXECUTION_PLAN_FIX_MODEL.md` dihapus dari working tree (digantikan dokumen `_FUSION`
di atas, mengikuti pola dokumen per-branch sebelumnya).

## 2. Baseline pytest — TEMUAN

Menjalankan `pytest` penuh **sebelum** perubahan apa pun ke `app/` menghasilkan **5 error**, bukan hijau:

```
ERROR tests/unit/test_api.py::test_health_check - NameError: name 'mock_get_db' is not defined
ERROR tests/unit/test_api.py::test_compounds_autocomplete_validation - NameError: ...
ERROR tests/unit/test_api.py::test_simulation_request_validation - NameError: ...
ERROR tests/unit/test_api.py::test_simulation_invalid_id - NameError: ...
ERROR tests/unit/test_api.py::test_simulation_valid_flow - NameError: ...
138 passed, 31 warnings, 5 errors in 6.57s
```

**Akar masalah:** `tests/unit/test_api.py` memiliki dua fixture `autouse=True`. Fixture pertama
(`override_db_for_unit_tests`) mendefinisikan closure `mock_get_db` secara lokal tapi tidak pernah
memakainya. Fixture kedua (`_override_get_db`) mereferensikan nama `mock_get_db` yang tidak ada di
scope-nya sendiri — sisa refaktor yang tidak lengkap (lihat docstring fixture: sebelumnya kode ini
top-level, dipindah jadi per-test fixture untuk mencegah kebocoran override `MagicMock` ke test
e2e/security lain). Ini bug pre-existing di `master`, **bukan** disebabkan pekerjaan `fusion`.

**Keputusan:** diperbaiki di F0 (bukan ditunda) karena:
- Perbaikannya trivial (menyatukan closure ke fixture yang benar-benar memakainya), tidak menyentuh
  kode `app/` yang termasuk dalam batas lingkup (§5 `PROJECT_FUSION.md`).
- DoD proyek mensyaratkan "seluruh pytest hijau" sebagai titik acuan regresi — baseline yang sudah
  merah membuat regresi tidak bisa dideteksi secara valid selama F1–F9.

**Setelah perbaikan:**

```
143 passed, 31 warnings in 4.18s
```

## 3. Baseline resmi untuk deteksi regresi

| Metrik | Nilai |
|---|---|
| Total test | **143 passed, 0 failed, 0 error** |
| Waktu total | ~4.2 detik |
| File test bermasalah | `tests/unit/test_api.py` (diperbaiki, lihat §2) |

Acuan regresi F1–F9: jumlah test **≥ 143**, seluruhnya hijau.

## 4. Tidak ada perubahan kode `app/` di luar perbaikan test di atas

Commit F0 mencakup: dokumen `_FUSION.md` (root), penghapusan dokumen `_FIX_MODEL.md` lama, direktori
`reports/`, dan perbaikan fixture `tests/unit/test_api.py`. Tidak ada perubahan pada
`fusion_service.py`, `exposure_evaluator.py`, `simulation_orchestrator.py`, `pbpk_engine.py`, atau
`allometric_service.py`.
