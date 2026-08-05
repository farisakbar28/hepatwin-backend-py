# C2_featurization.md -- Ekstraksi Fitur Molekul (ECFP4) dari Supabase

Snapshot Supabase: `ml/data/interim/compounds_snapshot.parquet` (lihat `.meta.json` untuk timestamp query).

## Tabel corong

| Tahap | n |
|---|---|
| Total baris di hepatwin_compounds | 1336 |
| is_simulatable = TRUE | 1231 |
| Multi-fragmen (mengandung '.') | 566 |
| Berhasil parse RDKit (standardize.py) | 1231 |
| Lolos standardisasi | 1231 |
| Fingerprint ECFP4 valid | 1231 |

**Dimensi fingerprint terverifikasi:** 1200 (MACCS 167 + ECFP4 1024 + SMARTS 9) untuk seluruh 1231 baris yang lolos.

**105 senyawa `is_simulatable = FALSE`:** tidak masuk pipeline ini secara desain -- `filter_simulatable()` memfilternya sebelum loop featurisasi dimulai (total 1336 - simulatable 1231 = 105).

## Kegagalan (dilaporkan eksplisit, bukan diam-diam dibuang)

**Gagal parse RDKit total:** 0

**Gagal setelah standardisasi (re-parse / fingerprint):** 0

## Catatan standardisasi (SS5.4 PROJECT_FIX_MODEL.md)

`ml/src/hepatwin_ml/data/standardize.py` yang dibawa dari branch `upscale` **sudah** memakai `LargestFragmentChooser` + `Uncharger` (bukan menolak SMILES multi-fragmen lewat `MixtureError`) -- diverifikasi langsung lewat eksekusi di atas, bukan diasumsikan dari deskripsi PROJECT_FIX_MODEL.md SS5.4. Tidak ada perubahan kode yang diperlukan pada file ini untuk C2; perbaikan yang diminta dokumen tersebut sudah ada di commit historis `upscale` (TU.2).

`standardize_eligible = False` (heavy atom count di luar rentang, atom non-organik, atau masih campuran setelah LargestFragmentChooser) muncul pada **43** dari 1231 baris yang berhasil fingerprint -- baris ini tetap punya fingerprint valid (dipakai saat inferensi bila pengguna memilih senyawa tsb.) tapi akan dikeluarkan dari korpus training di C5 bila juga tidak punya label biner atau melanggar constraint training lain.