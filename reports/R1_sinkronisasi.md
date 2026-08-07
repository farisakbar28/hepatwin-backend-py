# R1 -- Sinkronisasi `master` -> `fusion` & Arsip Laporan Usang

## 1. \U0001F6A8 Temuan di luar cakupan R1 asli: merge sebelumnya rusak

`PROJECT_FUSION_V23.md` SS2 mengasumsikan penyelarasan Mesin A sudah bersih kecuali satu baris impor
tidak terpakai. Verifikasi nyata (menjalankan `pytest`) menunjukkan itu **tidak akurat** -- commit merge
`95e53c7` ("resolve conflicts") meninggalkan `app/services/simulation_orchestrator.py` dalam kondisi
**tidak bisa di-import sama sekali**:

- `SyntaxError`: keyword argument `exposure_category` dikirim dua kali ke `SimulationResponse(...)`.
- Variabel tak terdefinisi: `t_parallel_start`, `t_exposure_start`, `t_ai`, `t_shap`, `t_pbpk` dipakai
  tanpa pernah di-assign (sisa refactor F6 yang tidak selesai digabung dengan alur v2.3 baru).
- Unpacking `asyncio.gather()` tidak konsisten: `ai_task`/`shap_task` dibungkus `_timed()` (mengembalikan
  tuple), `pbpk_task` tidak -- unpacking tiga-arah akan salah tipe walau syntax error di atas diperbaiki.
- `app/core/config.py` kehilangan `FUSION_AI_T_LOW`/`FUSION_AI_T_HIGH` (dipakai `fusion_service.py`,
  F2/F3) -- akan `AttributeError` begitu dipanggil.
- `app/models/schemas.py` kehilangan field `hotspot_intensity`, `hotspot_display_mode`, `evidence_note`
  (F4) dan `fusion_reason`, `thresholds_used`, `timing_ms` (F7) dari `SimulationResponse` -- padahal
  orchestrator masih menghitungnya (kode mati/tidak terpakai).

**Akibatnya:** `pytest` tidak bisa collect sama sekali (0 test berjalan) sebelum sesi ini dimulai --
bukan "beberapa test gagal karena perubahan Mesin A" seperti diantisipasi acceptance criteria R1 asli,
melainkan kegagalan total di level import.

**Diperbaiki** (di luar cakupan resmi R1, tapi prasyarat mutlak sebelum R1 apa pun bisa diverifikasi):
1. `simulation_orchestrator.py`: perbaiki unpacking tiga-tugas paralel (`pbpk_task` kini juga dibungkus
   `_timed()`), definisikan ulang `t_parallel_start`/`t_exposure_start`, hapus duplikasi kwarg
   `exposure_category`, kembalikan `hotspot_intensity`/`hotspot_display_mode`/`evidence_note`/
   `fusion_reason`/`thresholds_used`/`timing_ms` ke pemanggilan `SimulationResponse(...)`.
2. `app/core/config.py`: kembalikan `FUSION_AI_T_LOW=0.5458`/`FUSION_AI_T_HIGH=0.6866` (F2 -- nilai
   tidak berubah, PROJECT_FUSION_V23.md SS3.5 mengonfirmasi `dili_score` tidak dipengaruhi upgrade Mesin A).
3. `app/models/schemas.py`: kembalikan enam field yang hilang ke `SimulationResponse` (additive,
   tidak menyentuh field v2.3 yang sudah ada -- `shape_ratio_h_inv`, `exposure_index`, dst tetap utuh).

Sesuai prinsip kerja #3 (dokumen induk): ini "kegagalan adalah keluaran yang sah" -- dicatat apa adanya,
bukan disembunyikan di balik commit message generik.

## 2. Verifikasi nol divergensi Mesin A

```
git diff master fusion -- app/services/pbpk_engine.py app/services/pbpk_calibration.py app/services/allometric_service.py
```
**Kosong** -- ketiga file identik dengan `master`, tidak ada perubahan tidak sengaja dari branch `fusion`.

```
git diff master -- app/services/exposure_evaluator.py
```
Awalnya berbeda **satu baris** (`from app.core.config import settings`, tidak terpakai) -- persis sesuai
prediksi `PROJECT_FUSION_V23.md` SS2. Dihapus. Sekarang **kosong** -- identik `master`.

## 3. Status pytest pasca-sinkronisasi

Sebelum perbaikan R0 (di atas): **import gagal, 0 test collect.**

Setelah perbaikan:
```
177 passed, 1 failed
```

Satu kegagalan: `tests/e2e/test_d9_fusion_e2e.py::test_vno_safe_compound_reaches_ai_low_band` -- test ini
SENGAJA ditulis di F8 (siklus v2.1) untuk gagal loud bila `exposure_category` senyawa aman referensi
berubah dari `HIGH_EXPOSURE`/`MODERATE_EXPOSURE` ke `LOW_EXPOSURE`. **Itulah yang terjadi**: senyawa
sama (Calcitonin salmon, SMILES asli, skenario dosis wajar) kini mendapat `LOW_EXPOSURE` di bawah Mesin A
v2.3 -- sinyal awal yang POSITIF bahwa upgrade v2.3 berhasil menyelesaikan temuan
`F2_exposure_reachability_finding.md` (arsip). **Tidak diperbaiki di R1** -- pembuktian formal & sweep
skala penuh ada di R2/R3; test lama ini akan ditulis ulang di R3 setelah temuan resmi.

## 4. Arsip

Enam laporan v2.1 dipindah ke `reports/_v21_archive/` via `git mv` (riwayat git tetap utuh, bukan
hapus+buat baru): `F2_exposure_reachability_finding.md`, `F2_penurunan_ambang.md`,
`F5_audit_exposure.md`, `F9_limitations_fusion.md`, `F9_laporan_d7_d9.md`, `F9_jury_challenge.md`.
`reports/_v21_archive/README.md` ditambahkan menjelaskan konteks arsip.
