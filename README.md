# HepaTwin Backend API

FastAPI backend untuk skrining praklinis in-silico HepaTwin. PBPK Fase 1
adalah model 4-kompartemen linear, bolus tunggal, selama 24 jam. Output PBPK
adalah indeks paparan komputasional untuk riset/edukasi—bukan diagnosis,
rekomendasi dosis, atau keputusan terapi.

## Kontrak PBPK v2.3

- Simulasi hanya menerima `hepatwin_id` dari katalog tertutup dengan
  `is_simulatable = true`, dosis bolus tunggal, dan kovariat usia 0–100,
  jenis kelamin, berat, serta tinggi.
- Cmax/AUC dihitung oleh RK45. `cmax_auc_ratio` tetap tersedia hanya sebagai
  alias kompatibilitas untuk `shape_ratio_h_inv`; ia bukan magnitude exposure.
- Kategori paparan memakai `exposure_index = log1p(Cmax_L) + log1p(AUC_L)`
  dan kuantil calibration internal yang dibekukan. Lihat
  `reports/pbpk_exposure_calibration_v2_3.md`.
- BMI >= 30 menghasilkan `metabolic_risk_flag` dan tidak memberi penalty
  clearance otomatis.

## Menjalankan

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger tersedia pada `http://127.0.0.1:8000/docs`.

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

Response meliputi `cmax_hati`, `auc_hati`, `cmax_auc_ratio`,
`shape_ratio_h_inv`, `exposure_index`, `exposure_category`, dan provenance
calibration. `GET /api/v1/pbpk/debug` menampilkan seluruh parameter
alometrik serta metrik PBPK untuk validasi pakar.

## Verifikasi

```bash
python -m pytest tests/unit tests/e2e tests/security/test_is_simulatable_enforcement.py
```

Test RLS/database eksternal harus dijalankan hanya terhadap environment uji
terisolasi karena menggunakan kredensial service-role dan dapat menjalankan
CRUD.
