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
### `GET /health`
Endpoint health check yang memverifikasi ketersediaan dan status AI Engine serta PK/PD Engine.

### `POST /api/v1/simulate`
Menerima payload JSON untuk memicu simulasi. 

**Contoh Request (Mode Edukasi Mendalam - Paracetamol):**
```json
{
  "mode": "edukasi_mendalam",
  "compound_id": "paracetamol",
  "dose_mg_kg": 15.0
}
```

**Contoh Request (Mode Triase Umum - SMILES arbitrer):**
```json
{
  "mode": "triase_umum",
  "smiles_string": "CC(=O)NC1=CC=C(O)C=C1"
}
```

**Struktur Response:**
Mengembalikan objek `SimulationResponse` yang memuat `DILI_score`, `risk_level`, `damage_severity`, daftar `explainability` (gugus fungsi kontributor, hanya nama yang sudah divalidasi Farmasi — kosong bila belum ada), `visual_pattern` untuk rendering frontend, `supports_micro_zoom`, `disclaimer_hideable`, `model_status` (`"trained"` atau `"untrained_random_weights"` — lihat catatan di bawah), serta `time_series_pkpd` dan `nomogram_data` (khusus mode edukasi berbasis waktu untuk Paracetamol; saat ini terblokir sampai konstanta PD tervalidasi Farmasi, lihat PRD §13 item #1).

> **Catatan status model:** `models/model.pt` belum ada di repo ini, sehingga `HybridAIEngine` berjalan dengan bobot inisialisasi acak. Field `model_status="untrained_random_weights"` menandai ini secara eksplisit di setiap response — skor `DILI_score` pada kondisi ini TIDAK mencerminkan model terlatih apa pun (lihat `docs/AUDIT_TASKS.md` temuan F1).

## Struktur Direktori
```text
app/
├── api/             # Router & Endpoints FastAPI, beserta Dependency Injection
├── core/            # Konfigurasi aplikasi (CORS, dsb)
├── models/          # Skema data (Pydantic models)
├── services/        # Logika bisnis inti (Engine AI & PK/PD)
└── main.py          # Entry point aplikasi
data_preparation/    # Script bantu pemrosesan data (deduplikasi dataset)
```

## Lisensi & Keterbatasan
Penggunaan dataset eksternal tunduk pada standar metodologi riset (validasi terpisah dari *training data*). Kinerja AUC diuji pada dataset terisolasi secara *deduplicated*. Perangkat ini tidak dimaksudkan untuk mengganti uji coba praklinis (in-vivo/in-vitro) pada tahap validasi toksikologi sesungguhnya.
