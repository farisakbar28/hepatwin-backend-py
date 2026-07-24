# NOTICE.md — Atribusi Dataset & Pustaka Pihak Ketiga

Dasar: PRD §13 item #3 · EXECUTION_PLAN.md T7.3.

Dokumen ini mencatat sumber & lisensi dataset dan pustaka pihak ketiga yang
dipakai HepaTwin. Dibaca bersama `docs/DATA_PROVENANCE.md` (asal-usul rinci data).

---

## 1. Dataset

> ⚠️ **Perlu verifikasi manusia:** sitasi & sumber di bawah sudah diverifikasi,
> tetapi **teks lisensi/ketentuan penggunaan resmi** tiap dataset WAJIB
> dikonfirmasi ke halaman sumbernya sebelum publikasi/laporan akhir. Jangan
> menganggap tabel ini sebagai pernyataan lisensi final.

### 1.1 DILIrank v2.0 (data latih)

- **Sumber:** FDA Liver Toxicity Knowledge Base (LTKB).
- **Sitasi:** Olubamiwa et al. "DILIrank 2.0: An updated and expanded database
  for drug-induced liver injury risk based on FDA labeling and a literature
  review." *Drug Discovery Today* 2025;30(11):104485.
- **Catatan versi:** PRD §7/§8.4/§15 semula menyebut DILIrank v1 (Chen et al.,
  2016). Tim mengadopsi v2.0 — lihat keputusan di `docs/DATA_PROVENANCE.md` §1.1.
- **Lisensi:** data publik FDA (umumnya karya pemerintah AS / domain publik).
  **Verifikasi ketentuan resmi di halaman FDA LTKB sebelum publikasi.**

### 1.2 Xu et al. 2015 (external test set)

- **Sitasi:** Xu, Y., dkk. "Deep learning for drug-induced liver injury."
  *Journal of Chemical Information and Modeling* 2015;55(10):2085–2093.
- **Cara diperoleh:** ditarik lewat Therapeutics Data Commons
  (`tdc.single_pred.Tox(name='DILI')`, https://tdcommons.ai), lalu diekspor ke
  CSV polos. PyTDC dipakai sekali sebagai alat tarik data, bukan dependensi
  runtime (lihat `docs/DATA_PROVENANCE.md` §1.2).
- **Lisensi:** dataset dikurasi & didistribusikan TDC. **Verifikasi ketentuan
  penggunaan dataset DILI di tdcommons.ai + lisensi paper ACS sebelum publikasi.**

### 1.3 Dataset yang SENGAJA TIDAK dipakai

- **NCTR** — dikecualikan PRD §8.4 karena sumber historis penyusun DILIrank
  (risiko data leakage). Tidak diunduh, tidak dipakai.

### 1.4 Resolusi nama → SMILES

- **PubChem PUG-REST** (https://pubchem.ncbi.nlm.nih.gov) — layanan publik NIH,
  dipakai untuk resolusi nama obat DILIrank ke struktur SMILES. Data PubChem
  umumnya bebas dipakai; hormati kebijakan rate-limit resminya.

---

## 2. Pustaka Pihak Ketiga

Lisensi di bawah diambil dari **metadata paket yang benar-benar terinstal** di
`.venv` (bukan dari ingatan). Versi = versi yang terpasang saat dokumen ditulis
(2026-07-24). Untuk atribusi resmi, rujuk file LICENSE tiap paket.

### 2.1 Runtime / inference (masuk Docker image)

| Pustaka | Versi | Lisensi |
|---|---|---|
| RDKit | 2026.3.4 | BSD-3-Clause |
| FastAPI | 0.139.2 | MIT |
| Uvicorn | 0.51.0 | BSD-3-Clause |
| Pydantic | 2.13.4 | MIT |
| pydantic-settings | 2.14.2 | MIT |
| NumPy | 1.26.4 | BSD-3-Clause |
| SciPy | 1.15.3 | BSD-3-Clause |
| SHAP | 0.49.1 | MIT |
| LightGBM | 4.7.0 | MIT |
| scikit-learn | 1.7.2 | BSD-3-Clause |

> Catatan: bila gerbang T1.11 (`docs/GATE_DECISION_GNN.md`) diratifikasi ke
> `tabular`, PyTorch + PyG dikeluarkan dari runtime. Bila `gnn`, tambahkan:
> **PyTorch 2.13.0 (Apache-2.0 dan lisensi terkait)** dan
> **PyTorch Geometric 2.8.0 (MIT)**.

### 2.2 Hanya training/dev (TIDAK masuk Docker image)

| Pustaka | Versi | Lisensi |
|---|---|---|
| pandas | 2.3.3 | BSD-3-Clause |
| requests | 2.34.2 | Apache-2.0 |
| openpyxl | 3.1.5 | MIT |
| PyTDC | 0.4.1 | MIT |
| PyTorch | 2.13.0+cpu | Apache-2.0 (dan lisensi komponen terkait) |
| PyTorch Geometric | 2.8.0 | MIT |
| pytest, ruff, mypy | — | MIT / MIT / MIT |

---

*Diperbarui bila dependensi atau dataset berubah. Verifikasi lisensi dataset ke
sumber resmi sebelum laporan/publikasi akhir (PRD §13 #3).*
