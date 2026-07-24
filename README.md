# HepaTwin Backend API
FastAPI backend untuk HepaTwin: Digital Twin Hati Berbasis Kecerdasan Buatan untuk Simulasi Visual 3D Hepatotoksisitas Obat dan Triase Praklinis In-Silico Berbiaya Rendah.

## Tentang Repositori Ini
Backend ini menyediakan API komputasi untuk mendukung dua *mode* utama:
1. **Mode Edukasi Mendalam**: Menggunakan pemodelan farmakokinetik/farmakodinamik (PK/PD) berbasis persamaan diferensial untuk senyawa bermekanisme jelas (*Paracetamol*) dan prediksi probabilistik spasial (*Amoxicillin-Clavulanate*).
2. **Mode Triase Umum**: Menggunakan model AI hybrid (fitur substruktur RDKit + Graph Neural Network via PyTorch Geometric) untuk menerima input notasi kimia (SMILES) arbitrer dan mengembalikan skor DILI.

> **PERINGATAN KLINIS (DISCLAIMER WAJIB):** Seluruh output prediksi skor (DILI score) dari sistem ini, baik pada senyawa edukasi maupun input bebas, bersifat estimasi awal berbasis model riset *in-silico*. Ini **BUKAN** hasil uji toksisitas dan **BUKAN** pedoman klinis untuk pengaturan dosis, pengambilan keputusan medis, regulasi obat, atau penanganan pasien overdosis. Untuk penanganan toksisitas klinis, selalu merujuk pada protokol medis yang disahkan (seperti nomogram Rumack-Matthew untuk parasetamol) dan panduan dokter profesional.

## Tech Stack
* **Framework**: FastAPI (Python 3.x)
* **Validasi Data**: Pydantic
* **AI/Machine Learning Engine**: 
  * PyTorch (Graph Neural Network, GCN/GAT)
  * RDKit (Cheminformatics, SMILES processing, SMARTS substructures)
  * Scikit-Learn
  * SHAP (Model Explainability)
* **Scientific Computing**: NumPy, SciPy

## Instalasi
1. Pastikan Python 3.x sudah terpasang di sistem.
2. Buat dan aktifkan virtual environment:
   ```bash
   python -m venv venv
   # Di Windows:
   venv\Scripts\activate
   # Di Linux/Mac:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Salin `.env.example` ke `.env` dan sesuaikan nilainya.

## Menjalankan Server
Jalankan server menggunakan uvicorn:
```bash
uvicorn app.main:app --reload
```
API akan berjalan di `http://127.0.0.1:8000`. Dokumentasi interaktif (Swagger UI) dapat diakses di `http://127.0.0.1:8000/docs`.

## Endpoint Utama

| Method | Path | Fungsi | Status |
|---|---|---|---|
| GET | `/health` | Liveness + status engine (`ai_weights_loaded` membedakan server-nyala vs bobot-terlatih) | ✅ |
| GET | `/api/v1/compounds` | Daftar 2 senyawa flagship (paracetamol, amox_clav) | ✅ |
| POST | `/api/v1/validate-smiles` | Validasi SMILES cepat (RDKit saja, tanpa model) untuk input real-time | ✅ |
| POST | `/api/v1/simulate` | Endpoint utama simulasi | ✅ (lihat catatan Mesin A) |
| GET | `/api/v1/model-info` | Metadata + metrik model | ✅ (`metrics: null` sampai validasi eksternal resmi) |

Dokumentasi interaktif (Swagger UI) tersedia di `/docs`.

### `POST /api/v1/simulate`

**Contoh Request (Mode Triase Umum — SMILES bebas):**
```json
{ "mode": "triase_umum", "smiles_string": "CC(=O)NC1=CC=C(O)C=C1" }
```

**Contoh Request (Mode Edukasi Mendalam):**
```json
{ "mode": "edukasi_mendalam", "compound_id": "amox_clav", "dose_mg_kg": 15.0 }
```

**Response** (`SimulationResponse`) memuat antara lain: `DILI_score`, `risk_level`,
`damage_severity`, `explainability` (nama gugus tervalidasi Farmasi — **kosong**
sampai Farmasi memberi ACC), `visual_pattern`, `model_status`, `model_limitations`,
serta `time_series_pkpd`/`nomogram_data` (khusus parasetamol).

### Status kegunaan saat ini (penting untuk frontend)

| Jalur | Status | Keterangan |
|---|---|---|
| Triase umum (SMILES bebas) | ✅ berfungsi | Skor dari model tabular terlatih; `visual_pattern` selalu `heatmap_generik` |
| Edukasi — `amox_clav` | ✅ berfungsi | Digerakkan skor AI (Mesin B) |
| Edukasi — `paracetamol` | ⛔ **503 `E_MODEL_UNAVAILABLE`** | Mesin A (PK/PD) menunggu validasi konstanta Farmasi (PRD §13 #1). Gagal **rapi** dengan error typed, bukan 500 — frontend tampilkan pesan "menunggu validasi". |

> **Catatan model:** model DILI (Mesin B) **sudah terlatih pada data nyata**
> (DILIrank v2.0 + Xu et al. 2015), `model_status="trained"`. Validasi eksternal
> resmi masih di-re-seal (`metrics: null` di `/model-info`) sampai gerbang model
> diratifikasi tim — lihat `docs/GATE_DECISION_GNN.md` & `docs/DATA_PROVENANCE.md`.
> Yang masih menunggu Farmasi: simulasi PK/PD parasetamol + **nama** gugus di
> explainability (skornya nyata, penamaan gugusnya belum).

**Taksonomi error** (response `{code, detail}`, HTTP): `E_SMILES_INVALID` (422),
`E_MOL_TOO_LARGE` (422), `E_INORGANIC` (422), `E_MIXTURE` (422), `E_DOSE_RANGE`
(422), `E_REQUEST_INCOMPLETE` (422), `E_MODEL_UNAVAILABLE` (503).

## Struktur Direktori
```text
app/
├── api/             # Router & Endpoints FastAPI + Dependency Injection
├── chem/            # standardize, smarts_library, features (sumber tunggal featurizer)
├── core/            # config, cache, errors
├── models/          # Skema Pydantic
├── services/        # Engine AI (predictor/backend/explain) & PK/PD
├── artifacts/       # model.joblib (gitignored) + model_meta.json
└── main.py          # Entry point
ml/                  # Pipeline data & training (01-07), TIDAK masuk Docker image
data_preparation/    # (DEPRECATED — diganti ml/scripts/04_dedup_split.py; jangan dipakai)
```

## Lisensi & Keterbatasan
Penggunaan dataset eksternal tunduk pada standar metodologi riset (validasi terpisah dari *training data*). Kinerja AUC diuji pada dataset terisolasi secara *deduplicated*. Perangkat ini tidak dimaksudkan untuk mengganti uji coba praklinis (in-vivo/in-vitro) pada tahap validasi toksikologi sesungguhnya.
