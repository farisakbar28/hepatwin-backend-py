# HepaTwin Backend API

FastAPI backend untuk skrining praklinis in-silico HepaTwin. PBPK Fase 1
adalah model 4-kompartemen linear, bolus tunggal, selama 24 jam. Output PBPK
adalah indeks paparan komputasional untuk riset/edukasi—bukan diagnosis,
rekomendasi dosis, atau keputusan terapi.

## Kontrak Supabase v2.3

- Katalog tertutup 1.336 senyawa (1.231 simulatable).
- Format ID: `HTdddd` (misal `HT0012`).
- Separator `segment_list`: titik koma (`;`).
- Nilai `dili_concern`: raw canonical (misal `vMost-DILI-concern`).

## Endpoint PBPK

`POST /api/v1/simulate` menerima identifier katalog dan kovariat:

```json
{
  "hepatwin_id": "HT0012",
  "dosis_mg": 10500,
  "covariates": {
    "usia": 40,
    "jenis_kelamin": "L",
    "berat_badan_kg": 70,
    "tinggi_badan_cm": 168
  }
}
```

Response meliputi `cmax_liver_mg_l`, `auc_liver_mg_h_l` (dengan alias `cmax_hati`, `auc_hati`),
`shape_ratio_h_inv`, `exposure_index`, `exposure_category`, dan provenance
calibration. `GET /api/v1/pbpk/debug` menampilkan seluruh parameter
alometrik serta metrik PBPK untuk validasi pakar.

## Batasan (Known Limitations)

- Latensi request pertama `/simulate` ~8-10 detik (target PRD ≤5 s).
- Threshold fusi 0.30/0.70 bersifat provisional (Bab 8.3).
- Model PBPK Fase 1 adalah model linear bolus tunggal.

## Verifikasi

```bash
python -m pytest tests/unit tests/e2e tests/security/test_is_simulatable_enforcement.py
```

Test RLS/database eksternal harus dijalankan hanya terhadap environment uji
terisolasi karena menggunakan kredensial service-role dan dapat menjalankan
CRUD.
