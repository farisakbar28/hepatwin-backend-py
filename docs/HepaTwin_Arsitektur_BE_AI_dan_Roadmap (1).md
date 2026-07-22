# HepaTwin — Arsitektur Backend & AI + Roadmap Implementasi

**Versi:** 1.0
**Basis kepatuhan:** HepaTwin_PRD.md v1.0
**Cakupan dokumen:** Backend (FastAPI) dan AI/ML saja. Frontend React/R3F di luar cakupan, kecuali kontrak API.
**Aturan penyusunan:** Setiap keputusan teknis di dokumen ini harus dapat ditelusuri ke pasal PRD. Hal yang tidak diatur PRD ditandai eksplisit sebagai **[EKSTENSI]** dan memerlukan persetujuan. Hal yang berbeda dari PRD ditandai **[DEVIASI — PERLU KEPUTUSAN]**.

---

# BAGIAN A — MATRIKS KEPATUHAN

Sebelum arsitektur, ini pemetaan setiap komponen ke pasal PRD yang mengaturnya. Gunakan tabel ini saat review: kalau ada komponen yang tidak punya kolom "Pasal PRD", berarti itu di luar spesifikasi dan harus dipertanyakan.

| Komponen | Pasal PRD | Status |
|---|---|---|
| Dua mesin komputasi (PK/PD + AI) | §2.2, §7.1, §8.6 | Patuh |
| Mesin PK/PD parasetamol | §8.1 | Patuh |
| Amox-clav digerakkan skor AI | §8.2 | Patuh |
| Model AI hybrid RDKit + GNN | §7, §8.3 | Patuh, dengan gerbang kelayakan §13 #4 |
| Fallback model tabular | §13 #4 | Patuh (jalur resmi PRD) |
| Mode Triase = heatmap generik, tanpa pola zonal | §4.2, §7.1 langkah 3 | Patuh |
| Explainability nama gugus kimia | §8.5 | Patuh |
| Dataset training DILIrank | §7, §8.4 | Patuh |
| External test Xu et al. (2015) | §8.4 | Patuh |
| Deduplikasi SMILES kanonik wajib | §8.4 | Patuh |
| Eksklusi NCTR | §8.4 | Patuh |
| Target AUC 0,75–0,85 | §3, §8.3 | Patuh sebagai *target*; pelaporan aktual wajib per §8.3 |
| Baseline Mostafa et al. (2024) wajib dicantumkan | §3, §8.3 | Patuh |
| Disclaimer permanen Mode Triase | §14.2, §16 | Patuh, dengan catatan teknis (lihat A.1) |
| NFR waktu respons <3s / <5s | §6 | Patuh |
| Deployment Vercel + Railway | §7 | Patuh |
| Skema JSON response | §7.1 langkah 4 | Patuh sebagai basis, diperluas **[EKSTENSI]** |
| Applicability domain / abstain | — | **[EKSTENSI]** |
| Kalibrasi probabilitas | — | **[EKSTENSI]** |
| DILIrank 2.0 (1.336 obat) | PRD menyebut v1 (1.036) | **[DEVIASI — PERLU KEPUTUSAN]** |

## A.1 Temuan wajib ditindaklanjuti: teks disclaimer mengandung angka mati

PRD §14.2 mengunci teks disclaimer secara harfiah, termasuk angka:

> "Skor ini adalah estimasi awal berbasis model riset (AUC eksternal ~0,75–0,85), BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat."

Sementara PRD §8.3 dan §14.5 mewajibkan pelaporan angka aktual apa adanya, termasuk bila di bawah target.

Kedua pasal ini akan saling bertentangan jika AUC aktual di luar rentang 0,75–0,85 — disclaimer akan menampilkan angka yang tidak sesuai kenyataan, tepat di komponen yang tujuannya menjamin kejujuran.

**Solusi teknis (tidak mengubah maksud PRD):** jadikan angka pada disclaimer sebagai *template variable* yang diisi otomatis dari metadata model saat runtime.

```
"Skor ini adalah estimasi awal berbasis model riset
 (AUC eksternal aktual: {auc_external:.2f}, n_test={n_test}),
 BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat."
```

Backend menyediakan nilainya lewat `/api/v1/model-info`; frontend merender. Dengan cara ini teks disclaimer otomatis benar berapa pun hasil aktualnya, dan §14.2 tetap terpenuhi secara substansi. **Perlu persetujuan Ketua Tim + anggota Farmasi karena mengubah teks yang PRD tandai non-negotiable.**

---

# BAGIAN B — ARSITEKTUR SISTEM

## B.1 Peta lapisan

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (Vercel) — di luar cakupan dokumen ini              │
│ React + Tailwind + React Three Fiber + GSAP                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS / JSON
┌───────────────────────────▼─────────────────────────────────┐
│ API LAYER (FastAPI, Railway)                                 │
│  routes → validasi Pydantic → router mesin → serializer      │
└───────────┬───────────────────────────┬─────────────────────┘
            │                           │
┌───────────▼──────────────┐ ┌──────────▼──────────────────────┐
│ MESIN A — DETERMINISTIK  │ │ MESIN B — PROBABILISTIK          │
│ PK/PD parasetamol        │ │ Klasifikasi DILI dari SMILES     │
│ (PRD §8.1)               │ │ (PRD §8.2, §8.3)                 │
│                          │ │                                  │
│ • solusi closed-form Cp  │ │ • standardisasi RDKit            │
│ • ODE liver/NAPQI/GSH    │ │ • fitur SMARTS + fingerprint     │
│ • nomogram R-M           │ │ • model (GNN atau tabular)       │
│                          │ │ • SHAP → nama gugus              │
└───────────┬──────────────┘ └──────────┬──────────────────────┘
            │                           │
┌───────────▼───────────────────────────▼─────────────────────┐
│ LAPISAN BERSAMA                                              │
│ cache (SQLite) · registry artefak model · logging · error    │
└──────────────────────────────────────────────────────────────┘
```

## B.2 Routing tiga jalur (implementasi PRD §7.1 langkah 3)

PRD menetapkan tiga percabangan. Ini terjemahannya ke kode:

| Input | Mesin penggerak utama | Mesin pendamping | Output visual |
|---|---|---|---|
| `compound=paracetamol` | Mesin A (PK/PD) | Mesin B (skor risiko, pendamping) | Zonal sentrilobuler |
| `compound=amoxicillin_clavulanate` | Mesin B (skor AI) | — | Zonal portal/periportal |
| `mode=triase` + SMILES bebas | Mesin B (skor AI) | — | **Heatmap makro generik** |

Perhatikan baris ketiga. PRD §4.2 menempatkan prediksi pola mekanisme spesifik untuk Mode Triase **di luar scope**. Artinya kode tidak boleh berisi logika apa pun yang menebak kolestatik/hepatoselular untuk SMILES bebas. Field `visual_pattern` untuk mode triase **selalu** bernilai `heatmap_generik`, tanpa kondisional.

Tegakkan ini di level tipe, bukan hanya konvensi:

```python
# app/api/schemas.py
from typing import Literal
from pydantic import BaseModel

VisualPatternFlagship = Literal["sentrilobuler", "portal_periportal"]
VisualPatternTriase   = Literal["heatmap_generik"]   # satu-satunya nilai sah
```

Dengan tipe seperti ini, siapa pun yang nanti mencoba menambahkan pola zonal ke Mode Triase akan langsung gagal di type check — bukan lolos diam-diam ke produksi.

## B.3 Struktur repositori backend

```
backend/
├── app/
│   ├── main.py                     FastAPI app, CORS, middleware
│   ├── api/
│   │   ├── routes_health.py
│   │   ├── routes_compounds.py
│   │   ├── routes_simulate.py
│   │   ├── routes_model_info.py
│   │   └── schemas.py              seluruh Pydantic model
│   ├── engines/
│   │   ├── pkpd/
│   │   │   ├── absorption.py       Cplasma(t) closed-form (PRD §8.1 langkah 1)
│   │   │   ├── liver_napqi.py      sistem ODE (PRD §8.1 langkah 2–3)
│   │   │   ├── nomogram.py         garis 150/200 (PRD §8.1 validasi silang)
│   │   │   └── constants.py        parameter + sitasi, gerbang validasi Farmasi
│   │   └── ml/
│   │       ├── predictor.py        antarmuka tunggal predict(smiles)
│   │       ├── backend_tabular.py  implementasi fallback (PRD §13 #4)
│   │       ├── backend_gnn.py      implementasi GNN (PRD §8.3)
│   │       └── explain.py          SHAP → nama gugus (PRD §8.5)
│   ├── chem/
│   │   ├── standardize.py          RDKit sanitization + InChIKey
│   │   ├── smarts_library.py       kamus gugus, wajib ACC Farmasi
│   │   └── features.py             featurizer, dipakai training & inference
│   ├── core/
│   │   ├── config.py               pydantic-settings
│   │   ├── cache.py                SQLite key-value
│   │   ├── errors.py               taksonomi error
│   │   └── registry.py             pemuatan artefak + metadata versi
│   └── artifacts/
│       ├── model.joblib
│       ├── calibrator.joblib
│       ├── train_fps.npz           untuk applicability domain [EKSTENSI]
│       └── model_meta.json         versi, tanggal, metrik, n_train
├── tests/
├── requirements.txt                HANYA dependensi inference
└── Dockerfile
```

**Aturan kritis:** `app/chem/features.py` adalah satu-satunya sumber kebenaran featurization. Script training di folder `ml/` meng-import dari sini, bukan menyalinnya. Featurizer yang berbeda antara training dan inference adalah bug paling sulit dilacak di sistem ML, dan paling sering terjadi pada tim yang menyalin kode antar folder.

---

# BAGIAN C — MESIN A: PK/PD PARASETAMOL

Implementasi langsung PRD §8.1. Tidak ada kebebasan desain di sini — persamaannya sudah ditetapkan.

## C.1 Absorpsi oral (PRD §8.1 langkah 1)

```
Cplasma(t) = (F × Dose × ka) / (Vd × (ka − ke)) × (e^(−ke·t) − e^(−ka·t))
```

Parameter acuan yang PRD tetapkan dari Morse, Stanescu, Atkinson, & Anderson (2022), 116 sukarelawan dewasa sehat:

| Parameter | Nilai | Sumber |
|---|---|---|
| F | 0,86 | PRD §8.1 |
| CL | 24,0 L/jam/70kg | PRD §8.1 |
| V1 | 43,5 L/70kg | PRD §8.1 |
| ka | ≈3,47 jam⁻¹ (dari t½ absorpsi 12 menit) | PRD §8.1 |
| ke | ≈0,55 jam⁻¹ (CL/Vd) | PRD §8.1 |
| Lag time | 5,3 menit — **tidak dimasukkan** | PRD §8.1, batasan disadari |

Batasan yang PRD wajibkan didokumentasikan ke pengguna/juri: Morse et al. memakai model dua-kompartemen; HepaTwin menyederhanakan ke satu-kompartemen dan memakai V1 sebagai pendekatan Vd. Tempatkan teks ini di docstring modul **dan** di response API (field `model_limitations`), supaya tidak bisa hilang saat dokumen berpindah tangan.

**Kasus khusus numerik:** rumus di atas singular saat `ka == ke`. Walau tidak terjadi pada nilai acuan, tambahkan guard — kalau `abs(ka - ke) < 1e-6`, pakai bentuk limit `(F·Dose·ka·t/Vd)·e^(−ke·t)`. Ini kelas bug yang muncul hanya saat demo, tepat ketika seseorang menggeser slider ke nilai ekstrem.

## C.2 Sistem ODE hati (PRD §8.1 langkah 2–3)

```
dCliver/dt  = k_in × Cplasma(t) − k_elim × Cliver(t)
d[NAPQI]/dt = k_meta × Cliver(t) − k_GSH × [GSH](t) × [NAPQI](t)
```

Pemicu visual (PRD §8.1): `[NAPQI](t) / [GSH]₀ > θ_threshold` → nekrosis zona sentrilobuler.

Implementasi: `scipy.integrate.solve_ivp` dengan metode `LSODA`. Sistem ini menjadi *stiff* pada skenario overdosis, dan solver eksplisit seperti `RK45` akan melambat drastis atau gagal konvergen.

Catatan: PRD §8.1 langkah 3 menuliskan persamaan NAPQI dan GSH sebagai satu baris yang saling bergantung. Untuk `solve_ivp` kamu perlu persamaan GSH eksplisit sebagai state ketiga. **Bentuk persamaan GSH dan nilai laju sintesisnya adalah bagian dari item validasi Farmasi**, bukan sesuatu yang boleh diasumsikan engineer.

## C.3 Gerbang konstanta — mekanisme penegakan

PRD §13 item #1 menandai validasi k_in, k_elim, k_meta, k_GSH, θ_threshold sebagai **KRITIS**. Jangan andalkan ingatan; tegakkan lewat kode:

```python
# app/engines/pkpd/constants.py
from dataclasses import dataclass

@dataclass(frozen=True)
class PDConstant:
    value: float | None
    unit: str
    citation: str | None
    validated_by_pharmacy: bool = False

PD_CONSTANTS = {
    "k_in":        PDConstant(None, "1/jam", None),
    "k_elim":      PDConstant(None, "1/jam", None),
    "k_meta":      PDConstant(None, "1/jam", None),
    "k_GSH":       PDConstant(None, "1/(mM·jam)", None),
    "theta_thr":   PDConstant(None, "rasio", None),
}

def assert_ready():
    missing = [k for k, c in PD_CONSTANTS.items()
               if c.value is None or not c.validated_by_pharmacy or not c.citation]
    if missing:
        raise RuntimeError(
            f"Konstanta PD belum tervalidasi Farmasi: {missing}. "
            "Lihat PRD §13 item #1."
        )
```

Panggil `assert_ready()` saat startup aplikasi. Aplikasi menolak menyala selama konstanta belum lengkap. Ini mencegah skenario terburuk: angka karangan lolos ke demo dan ditanyakan juri.

## C.4 Validasi silang nomogram (PRD §8.1)

PRD mewajibkan Cplasma(t) pada rentang 4–24 jam konsisten posisinya terhadap garis 150/200.

```python
def nomogram_line(t_hours: float, anchor: float) -> float:
    """anchor=150 (garis pengobatan) atau 200 (garis asli Rumack-Matthew 1975).
    Peluruhan mengacu waktu-paruh referensi 4 jam. Berlaku 4 ≤ t ≤ 24.
    Sumber: PRD §8.1; verifikasi parameter ke sumber primer per PRD §13 #1."""
    if not 4.0 <= t_hours <= 24.0:
        raise ValueError("Nomogram hanya berlaku 4–24 jam pasca-konsumsi")
    return anchor * 2 ** (-(t_hours - 4.0) / 4.0)
```

**Parameter peluruhan garis nomogram termasuk item verifikasi Farmasi** per PRD §13 #1 ("Parameter kalibrasi nomogram (150/200) juga wajib diverifikasi ke sumber primer"). Jangan anggap konstanta 4 jam di atas sebagai final sampai dikonfirmasi.

Test yang harus lulus:
- Dosis terapetik (≈15 mg/kg) → kurva jauh di bawah garis 150 sepanjang 4–24 jam
- Dosis overdosis besar → kurva memotong ke atas garis 150 pada rentang tersebut
- Nilai di t=4 jam untuk garis 150 tepat 150 µg/mL

---

# BAGIAN D — MESIN B: MODEL AI

## D.1 Antarmuka tunggal, dua implementasi

PRD §8.3 menetapkan arsitektur hybrid RDKit + GNN. PRD §13 #4 menetapkan fallback tabular bila GNN tidak layak dalam timeline. Desain yang benar adalah **satu antarmuka dengan dua implementasi di baliknya**, sehingga keputusan gerbang kelayakan tidak memaksa penulisan ulang API.

```python
# app/engines/ml/predictor.py
from typing import Protocol

class DILIBackend(Protocol):
    name: str
    version: str
    def predict_proba(self, mol) -> float: ...
    def explain(self, mol) -> list[dict]: ...

def get_backend() -> DILIBackend:
    """Dipilih lewat env var ML_BACKEND = 'gnn' | 'tabular'."""
```

Route, skema response, dan frontend tidak berubah apa pun antara kedua jalur. Yang berubah hanya isi folder `artifacts/` dan satu variabel environment.

## D.2 Lapisan struktural (wajib di kedua jalur — PRD §8.3 komponen 1, §8.5)

Fitur substruktur SMARTS adalah **komponen wajib**, bukan opsional, karena PRD §8.5 mensyaratkan explainability berupa nama gugus kimia dan melarang indeks fitur abstrak.

```python
# app/chem/smarts_library.py
SMARTS_LIBRARY: dict[str, str] = {
    "cincin_beta_laktam":  "C1C(=O)N(C1)",
    "nitroaromatik":       "[c][N+](=O)[O-]",
    "anilin":              "[NX3;H2,H1][c]",
    "fenol":               "[OX2H][c]",
    "asam_karboksilat":    "[CX3](=O)[OX2H1]",
    "sulfonamida":         "[SX4](=O)(=O)[NX3]",
    "hidrazin":            "[NX3][NX3]",
    "tiofen":              "c1ccsc1",
    "furan":               "c1ccoc1",
    "epoksida":            "C1OC1",
    # lanjutkan bersama anggota Farmasi
}
```

PRD §13 item #2 dan §8.5 menandai pemetaan gugus → istilah farmakologis sebagai **KRITIS** dan wajib divalidasi Farmasi. Tegakkan seperti konstanta PD:

```python
SMARTS_VALIDATED_BY_PHARMACY: set[str] = set()   # diisi setelah ACC tertulis

def validated_library() -> dict[str, str]:
    return {k: v for k, v in SMARTS_LIBRARY.items()
            if k in SMARTS_VALIDATED_BY_PHARMACY}
```

Explainability hanya boleh menampilkan gugus dari `validated_library()`. Gugus yang belum di-ACC boleh dipakai sebagai fitur model, tapi **tidak boleh muncul di UI dengan nama farmakologis** — karena nama yang salah di media pembelajaran lebih merusak daripada tidak ada nama.

## D.3 Featurization

```python
# app/chem/features.py
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator, Descriptors, Crippen
from app.chem.smarts_library import SMARTS_LIBRARY

_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

_DESCRIPTORS = [
    ("mw", Descriptors.MolWt), ("logp", Crippen.MolLogP),
    ("tpsa", Descriptors.TPSA), ("hbd", Descriptors.NumHDonors),
    ("hba", Descriptors.NumHAcceptors), ("rotb", Descriptors.NumRotatableBonds),
    ("arom", Descriptors.NumAromaticRings), ("heavy", Descriptors.HeavyAtomCount),
    ("fsp3", Descriptors.FractionCSP3), ("rings", Descriptors.RingCount),
]

_SMARTS_COMPILED = {k: Chem.MolFromSmarts(v) for k, v in SMARTS_LIBRARY.items()}

def feature_names() -> list[str]:
    return ([f"ecfp_{i}" for i in range(2048)]
            + [n for n, _ in _DESCRIPTORS]
            + [f"smarts::{k}" for k in _SMARTS_COMPILED])

def featurize(mol) -> np.ndarray:
    fp = np.asarray(_gen.GetFingerprintAsNumPy(mol), dtype=np.float32)
    desc = np.asarray([f(mol) for _, f in _DESCRIPTORS], dtype=np.float32)
    smarts = np.asarray([float(mol.HasSubstructMatch(p))
                         for p in _SMARTS_COMPILED.values()], dtype=np.float32)
    return np.concatenate([fp, desc, smarts])
```

Prefiks `smarts::` pada nama fitur bukan kosmetik — itu yang memungkinkan `explain.py` menyaring kontribusi SHAP hanya dari fitur yang punya nama farmakologis, sesuai PRD §8.5.

## D.4 Jalur GNN (PRD §8.3, jalur utama sesuai spesifikasi)

Spesifikasi PRD: representasi graf (atom = node, ikatan = edge), GCN/GAT 1–2 layer via PyTorch Geometric, digabung (concatenated) dengan lapisan struktural sebelum klasifikasi akhir, mengikuti pola InterDILI (Lee & Yoo, 2024).

Rancangan konkret:

```
Molekul
 ├─ cabang graf:  atom features → GCNConv(64) → ReLU → GCNConv(64)
 │                → global_mean_pool → vektor 64-d
 └─ cabang struktural: [ECFP 2048 + deskriptor 10 + SMARTS n]
                       → Linear(128) → ReLU
                                    ↓
                     concat(64 + 128) → Dropout(0.3)
                                      → Linear(64) → ReLU
                                      → Linear(1) → sigmoid
```

Fitur node atom minimal: nomor atom (one-hot pada himpunan organik), derajat, muatan formal, jumlah H, aromatisitas, hibridisasi, keanggotaan cincin.

Catatan implementasi yang menentukan berhasil-tidaknya:
- Ukuran training set kecil (§D.7). Pakai regularisasi kuat: dropout 0,3–0,5, weight decay, early stopping pada validation fold.
- `class_weight` seimbang, karena distribusi DILIrank tidak 50:50.
- Seed tetap dan `torch.use_deterministic_algorithms(True)` supaya hasil reproducible saat dilaporkan.

## D.5 Gerbang kelayakan GNN (implementasi PRD §13 #4)

PRD mewajibkan uji kelayakan dengan fallback siap. Gerbang harus punya kriteria objektif dan batas waktu, ditetapkan **sebelum** eksperimen dimulai — kalau tidak, keputusan akan didorong emosi ("sudah terlanjur seminggu, lanjut saja").

**Waktu evaluasi:** akhir minggu ke-2 Sprint 1.

**Lulus jika SEMUA terpenuhi:**

| Kriteria | Ambang |
|---|---|
| AUROC CV internal GNN vs baseline tabular | GNN unggul ≥ 0,02 |
| Pipeline training stabil | 5 fold selesai tanpa crash, hasil reproducible |
| Ukuran Docker image inference | ≤ 1,5 GB |
| Waktu inferensi 1 molekul (cold cache) | ≤ 2 detik |
| SHAP pada cabang struktural berfungsi | Ya |

**Gagal salah satu → pivot ke `ML_BACKEND=tabular`**, dan catat keputusan di laporan akhir sesuai PRD §13 #4 ("revisi klaim novelty sesuai kondisi aktual").

Ambang 1,5 GB dan 2 detik bukan angka sembarang: NFR PRD §6 menetapkan Mode Triase < 5 detik, dan cold start container di free tier sudah memakan sebagian besar anggaran itu.

## D.6 Jalur tabular (fallback resmi PRD §13 #4)

```python
import lightgbm as lgb

model = lgb.LGBMClassifier(
    n_estimators=400, learning_rate=0.05, num_leaves=31,
    subsample=0.8, colsample_bytree=0.6,
    class_weight="balanced", random_state=42,
)
```

Keunggulan operasional yang relevan dengan NFR: SHAP `TreeExplainer` bersifat eksak dan cepat untuk model pohon, sehingga explainability PRD §8.5 terpenuhi tanpa biaya waktu inferensi tambahan yang berarti.

## D.7 Dataset & validasi (PRD §8.4)

| Tahap | Dataset | Peran |
|---|---|---|
| Training | DILIrank (Chen et al., 2016) | PRD §8.4 |
| External test | Xu et al. (2015), 344–475 senyawa | PRD §8.4 |
| **Dilarang** | NCTR | PRD §8.4 — sumber historis DILIrank, risiko leakage |

**Deduplikasi wajib (PRD §8.4).** PRD menyebut pencocokan SMILES kanonik via RDKit. Rekomendasi teknis: gunakan **blok pertama InChIKey (14 karakter)** sebagai kunci pencocokan, bukan string SMILES kanonik langsung.

Alasannya faktual: SMILES kanonik masih membedakan stereoisomer dan bentuk tautomer, sehingga dua entri yang secara konektivitas identik bisa lolos sebagai "berbeda" dan menghasilkan leakage yang justru ingin dicegah PRD. Blok pertama InChIKey merepresentasikan konektivitas molekul. Ini **memperkuat** maksud PRD §8.4, bukan menyimpanginya — tetap catat sebagai penyempurnaan teknis di laporan.

Senyawa tumpang tindih dihapus **dari external test set**, bukan dari training — agar kapasitas training maksimal sementara independensi test terjamin.

**Konsekuensi yang harus diantisipasi:** DILIrank dan Xu et al. sama-sama bersumber dari pool obat yang beririsan. Setelah dedup, external test bisa menyusut jauh di bawah 344. Laporkan ukuran akhirnya apa adanya beserta interval kepercayaan bootstrap — test set kecil berarti CI lebar, dan itu fakta metodologis yang wajib disampaikan, bukan disembunyikan.

## D.8 Pelaporan performa (PRD §3, §8.3, §14.5)

Metrik wajib: akurasi, AUC, sensitivity, specificity, MCC — sesuai PRD §3 tujuan #5.

Tabel pembanding wajib di laporan akhir:

| Model | Sumber | Angka |
|---|---|---|
| Baseline RF/MLP | Mostafa, Howle, & Chen (2024) | akurasi 0,631 · MCC 0,245 |
| Target HepaTwin | PRD §3, §8.3 | AUC 0,75–0,85 |
| **HepaTwin aktual** | eksperimen | *diisi apa adanya* |

PRD §8.3 dan §14.5 menegaskan: angka aktual wajib dilaporkan **termasuk jika di bawah target**. Sediakan mekanismenya sejak awal — `model_meta.json` menyimpan angka aktual, `/api/v1/model-info` menyajikannya, disclaimer merendernya (lihat A.1). Dengan begitu kejujuran menjadi properti sistem, bukan sekadar niat baik.

**[EKSTENSI] Uji permutasi (y-randomization).** Acak label training 20×, latih ulang, bandingkan distribusi AUROC acak terhadap model asli. Murah (menit) dan merupakan bukti langsung bahwa model belajar sinyal, bukan menghafal noise. Tidak diminta PRD, tapi memperkuat tujuan #5.

## D.9 [EKSTENSI] Kalibrasi dan applicability domain

Dua penambahan di luar PRD. Diajukan karena keduanya melayani prinsip non-negosiabel PRD §2 dan §14 (produk tidak boleh overclaim), tetapi **memerlukan persetujuan** karena menambah perilaku yang belum dispesifikasikan.

**Kalibrasi** — `CalibratedClassifierCV(method="isotonic")` plus pelaporan Brier score dan reliability curve. Tanpa ini, angka 0,58 yang tampil di UI tidak punya makna probabilistik yang bisa dipertanggungjawabkan kepada mahasiswa.

**Applicability domain** — rata-rata kemiripan Tanimoto terhadap 3 tetangga terdekat di training set. Di bawah ambang empiris, API mengembalikan `abstained: true` alih-alih skor.

```python
from rdkit import DataStructs
import numpy as np

def ad_similarity(query_fp, train_fps, k: int = 3) -> float:
    sims = np.asarray(DataStructs.BulkTanimotoSimilarity(query_fp, train_fps))
    return float(np.mean(np.sort(sims)[-k:]))
```

Penetapan ambang: plot akurasi model terhadap similarity pada test set, ambil titik di mana akurasi jatuh. Ini memberi pembenaran empiris, bukan angka pilihan sendiri.

**Dampak ke frontend:** keadaan abstain adalah respons 200 dengan `abstained: true`, bukan error. Frontend perlu merender keadaan ini (organ netral, panel skor diganti pesan). Karena berdampak lintas komponen, keputusannya milik Ketua Tim.

---

# BAGIAN E — KONTRAK API

## E.1 Daftar endpoint

| Method | Path | Fungsi | Dasar |
|---|---|---|---|
| GET | `/health` | Liveness probe | Operasional |
| GET | `/api/v1/compounds` | Daftar senyawa flagship + metadata | PRD §9.3 dropdown |
| POST | `/api/v1/validate-smiles` | Validasi cepat untuk frontend | PRD §7.1 langkah 1 |
| POST | `/api/v1/simulate` | Endpoint utama | PRD §7.1 langkah 2–4 |
| GET | `/api/v1/model-info` | Versi + metrik aktual model | PRD §8.3, §14.5 · **[EKSTENSI]** |

## E.2 Request

```python
class SimulateRequest(BaseModel):
    mode: Literal["edukasi_mendalam", "triase_umum"]
    compound: Optional[Literal["paracetamol", "amoxicillin_clavulanate"]] = None
    smiles: Optional[str] = Field(None, max_length=500)
    dose_mg_kg: Optional[float] = Field(None, gt=0, le=1000)
    duration_h: int = Field(24, ge=1, le=72)
```

Validasi silang: mode `edukasi_mendalam` mewajibkan `compound`; mode `triase_umum` mewajibkan `smiles`. Gunakan `model_validator` Pydantic, jangan `if` tersebar di route.

## E.3 Response

PRD §7.1 langkah 4 memberi contoh minimal. Berikut perluasannya — field asli PRD ditandai, sisanya **[EKSTENSI]**:

```json
{
  "input_smiles": "CC(=O)Nc1ccc(O)cc1",
  "mode": "triase_umum",
  "DILI_score": 0.58,
  "model_confidence_note": "skor berbasis model riset, bukan hasil uji klinis",
  "explainability": ["cincin beta-laktam", "anilin"],
  "visual_pattern": "heatmap_generik",

  "engine": "ml_probabilistic",
  "model_version": "hepatwin-tabular-1.0.0",
  "abstained": false,
  "applicability_domain": { "in_domain": true, "similarity": 0.71 },
  "score_interval": { "low": 0.41, "high": 0.79 },
  "model_limitations": ["..."],
  "disclaimer": "Skor ini adalah estimasi awal berbasis model riset (AUC eksternal aktual: 0.6X, n_test=NNN), BUKAN hasil uji toksisitas dan BUKAN dasar keputusan keamanan obat."
}
```

Empat field pertama setelah baris kosong adalah yang paling penting untuk diperjuangkan ke Ketua Tim:

- `engine` — frontend tidak boleh menebak mesin mana yang dipakai; label UI harus mengikuti nilai ini
- `model_version` — membuat setiap screenshot di laporan dapat ditelusuri ke model tertentu
- `abstained` — konsekuensi langsung dari D.9
- `disclaimer` — dikirim server, sehingga teks tidak bisa tertinggal versi lama di frontend

Untuk mode `edukasi_mendalam` dengan parasetamol, response memuat tambahan: array `cplasma_curve`, `napqi_gsh_ratio_curve`, `nomogram` (garis 150 & 200 pada rentang waktu yang sama), dan `threshold_crossed_at_h`. `engine` bernilai `pkpd_deterministic`.

## E.4 Taksonomi error

| Kode | Kondisi | Pesan pengguna | HTTP |
|---|---|---|---|
| `E_SMILES_INVALID` | RDKit gagal parse | "Notasi SMILES tidak dapat dibaca" | 422 |
| `E_MOL_TOO_LARGE` | > 100 atom berat | "Molekul di luar cakupan model" | 422 |
| `E_INORGANIC` | atom di luar himpunan organik | "Senyawa anorganik/logam tidak didukung" | 422 |
| `E_MIXTURE` | masih campuran setelah standardisasi | "Masukkan satu senyawa tunggal" | 422 |
| `E_DOSE_RANGE` | dosis di luar batas | "Dosis di luar rentang simulasi" | 422 |
| `E_MODEL_UNAVAILABLE` | artefak gagal dimuat | "Layanan model sedang tidak tersedia" | 503 |
| `W_OUT_OF_DOMAIN` | AD di bawah ambang | (abstain, bukan error) | 200 |

Baris terakhir penting: abstain bukan kegagalan. Frontend harus memperlakukannya sebagai keadaan sah.

## E.5 Caching

```
cache_key = sha256(f"{engine}|{model_version}|{inchikey_block1}|{dose}|{duration}")
```

`model_version` wajib masuk kunci. Tanpa itu, setelah deploy model baru, cache lama akan menyajikan hasil model lama tanpa terdeteksi.

Backend SQLite. Redis hanya jika terbukti perlu — menambah layanan berarti menambah titik gagal saat demo.

## E.6 Keamanan & NFR

- Rate limit `/simulate`: 30 req/menit per IP
- CORS: whitelist domain Vercel proyek saja, tidak `*`
- Batas ukuran body request
- Stack trace tidak pernah masuk response
- Target NFR PRD §6: < 3 detik (Edukasi), < 5 detik (Triase)

---

# BAGIAN F — DEPLOYMENT

## F.1 Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxrender1 libxext6 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`requirements.txt` backend hanya berisi dependensi **inference**. Jangan sertakan pustaka training, plotting, atau PyTDC. Setiap MB berdampak pada cold start, yang berdampak langsung pada NFR §6.

## F.2 Mitigasi cold start

Free tier Railway menidurkan container saat idle. Ini risiko langsung terhadap NFR §6 dan terhadap demo di depan juri.

Tiga lapis:
1. **Precompute demo set** — hitung hasil untuk ~50 senyawa terkurasi, simpan sebagai JSON statis yang di-serve frontend. Demo utama tidak menyentuh backend.
2. **Keep-alive** — cron eksternal ping `/health` tiap 10 menit.
3. **Rekaman cadangan** — video demo sudah menjadi item PRD §13 #10; jadikan juga jaring pengaman bila jaringan venue bermasalah.

---

# BAGIAN G — STRATEGI PENGUJIAN

| Lapis | Cakupan | Contoh kasus wajib |
|---|---|---|
| Unit — chem | Standardisasi | Garam ter-strip; SMILES invalid → None; InChIKey stabil |
| Unit — PK/PD | Persamaan | `assert_ready()` gagal saat konstanta kosong; nomogram t=4 → 150; guard ka≈ke |
| Unit — ML | Featurizer | Panjang vektor konsisten; nama fitur sinkron dengan artefak |
| Integrasi | Endpoint | 2 flagship; SMILES valid; SMILES invalid; molekul besar; senyawa di luar domain |
| Kontrak | Skema | Response mode triase **selalu** `visual_pattern="heatmap_generik"` |
| Regresi data | Pipeline | Assert nol overlap InChIKey train ↔ external test |
| Performa | NFR §6 | Edukasi < 3 s; Triase < 5 s |

Dua test yang paling bernilai dan paling sering dilupakan: **assert nol overlap** (menjaga validitas seluruh angka performa) dan **assert `heatmap_generik`** (menjaga batas scope PRD §4.2 tetap tertegak walau tim berganti-ganti kode).

---

# BAGIAN H — ROADMAP

Dipetakan ke sprint plan PRD §11. Kolom "Fokus BE/AI" adalah pekerjaan yang dicakup dokumen ini.

## Sprint 0 — Fondasi (1 minggu)

| Hari | Pekerjaan |
|---|---|
| 1 | Repo, struktur folder Bagian B.3, venv, RDKit terverifikasi |
| 2 | FastAPI kerangka: `/health`, `/api/v1/compounds`, Swagger aktif |
| 3 | `config.py`, `errors.py`, `cache.py` (SQLite), CORS |
| 4 | `schemas.py` lengkap; kirim draf kontrak API ke Ketua Tim untuk persetujuan |
| 5 | Mock mode aktif (response valid tanpa model) → frontend tidak terblokir |

**Selesai bila:** frontend bisa memanggil `/simulate` mock dan mendapat JSON berbentuk final.

**Aksi paralel hari 1:** kirim ke anggota Farmasi paket permintaan validasi sekaligus — konstanta PD (§13 #1), parameter nomogram (§13 #1), daftar SMARTS (§13 #2), pola histologis amox-clav (§13 #2). PRD §12 sudah menandai risiko Farmasi jadi bottleneck; kirim batch di awal, bukan satu per satu.

## Sprint 1 — Data & AI Engine Dasar (3 minggu)

PRD sudah memperpanjang sprint ini 2→3 minggu karena kompleksitas dataset + GNN.

**Minggu 1 — data**

| Hari | Pekerjaan |
|---|---|
| 1 | Unduh DILIrank; unduh Xu et al. (2015); verifikasi lisensi (PRD §13 #3) |
| 2–3 | Resolusi nama obat → SMILES (lihat catatan di bawah) |
| 4 | `standardize.py`: strip garam, netralisasi, canonical SMILES, InChIKey |
| 5 | Dedup InChIKey blok-1; split scaffold; assert nol overlap; tulis `reports/data_curation.md` |

**Catatan teknis untuk hari 2–3.** DILIrank berisi nama senyawa, bukan SMILES. Diperlukan langkah resolusi nama → struktur (mis. lewat PubChem PUG-REST) sebelum data bisa dipakai. Ini langkah nyata yang belum tercantum eksplisit di PRD §8.4 dan mudah luput dari estimasi waktu.

Yang perlu disiapkan: caching hasil ke disk (script akan dijalankan berulang), penghormatan terhadap rate limit layanan yang dipakai (cek dokumentasi resminya saat implementasi), strategi fallback untuk nama berbentuk garam, dan pembuangan entri biologik (`-mab`, `-cept`, protein) yang tidak punya SMILES bermakna. Tingkat keberhasilan resolusi otomatis tidak akan 100%; catat berapa yang gagal dan alasannya di `reports/data_curation.md`.

**Minggu 2 — baseline + gerbang GNN**

| Hari | Pekerjaan |
|---|---|
| 1 | `features.py` final; kunci `feature_names()` |
| 2 | Baseline tabular LightGBM, 5-fold CV → **angka pertama** |
| 3–4 | Implementasi GNN per D.4 |
| 5 | **Evaluasi gerbang D.5 → keputusan tertulis `ML_BACKEND`** |

Keputusan gerbang dicatat sebagai dokumen singkat (kriteria, angka, kesimpulan) untuk lampiran laporan akhir, sesuai amanat PRD §13 #4 tentang revisi klaim novelty.

**Minggu 3 — produksi + validasi eksternal**

| Hari | Pekerjaan |
|---|---|
| 1 | Latih model final pada jalur terpilih |
| 2 | `explain.py`: SHAP → filter `smarts::` → nama gugus tervalidasi (§8.5) |
| 3 | **[EKSTENSI]** kalibrasi + applicability domain, bila disetujui |
| 4 | **Buka external test set — jalankan sekali.** Metrik lengkap + CI bootstrap. Uji permutasi |
| 5 | `model_meta.json`; endpoint `/model-info`; `reports/external_validation.md`; bekukan commit |

Aturan yang tidak boleh dilanggar: setelah external test dibuka di hari 4, dilarang kembali menyetel model berdasarkan angka tersebut. Jika terpaksa, statusnya berubah dan wajib dinyatakan di laporan.

## Sprint 2 — PK/PD Integration (1 minggu)

PRD §11 menyarankan sprint ini diparalelkan dengan Sprint 1 bila waktu terbatas. **Ambil saran itu** — mulai begitu Sprint 0 selesai, karena PK/PD tidak bergantung pada model AI sama sekali.

| Hari | Pekerjaan |
|---|---|
| 1 | `absorption.py` + guard ka≈ke; unit test |
| 2 | `constants.py` + `assert_ready()`; integrasikan hasil validasi Farmasi |
| 3 | `liver_napqi.py` dengan `solve_ivp`/LSODA |
| 4 | `nomogram.py` + test validasi silang (PRD §8.1) |
| 5 | Integrasi ke `/simulate`; plot validasi tersimpan untuk laporan |

**Blocker yang harus dipantau:** bila hingga akhir Sprint 1 konstanta PD belum divalidasi Farmasi, eskalasi ke dosen pembimbing. PRD §13 menandai ini KRITIS; `assert_ready()` akan menahan aplikasi menyala, jadi keterlambatan di sini memblokir Mode Edukasi Mendalam sepenuhnya.

## Sprint 3 — 3D Visual & Mode Triase (2 minggu)

Fokus utama frontend. Dukungan BE/AI:

- Endpoint `/validate-smiles` responsif untuk validasi saat mengetik
- Stabilkan bentuk response kedua mode
- **Verifikasi kontrak:** pastikan mode triase tidak pernah mengirim pola zonal (test Bagian G)
- Optimasi jalur triase agar memenuhi NFR < 5 detik

## Sprint 4 — Dashboard & UX (1 minggu)

- Sediakan data panel nomogram dalam bentuk siap render
- Sediakan teks disclaimer dari server dengan angka aktual (Bagian A.1)
- Sediakan `model_limitations` untuk panel batasan model

## Sprint 5 — Evaluasi Dampak (1 minggu)

Dipimpin Farmasi (PRD §10, §12). Dukungan BE/AI: pastikan lingkungan stabil selama sesi, precompute skenario yang akan dipakai, siapkan mode offline bila jaringan lab bermasalah.

## Sprint 6 — Integrasi & Testing (1 minggu)

| Hari | Pekerjaan |
|---|---|
| 1–2 | End-to-end kedua mode; perbaikan bug kontrak |
| 3 | Uji performa terhadap NFR §6; optimasi bila meleset |
| 4 | Deploy Railway; CORS; rate limit; keep-alive; precompute demo set |
| 5 | Uji beban ringan; verifikasi cold start |

## Sprint 7 — Finalisasi (1 minggu)

| Hari | Pekerjaan |
|---|---|
| 1 | `model_card.md`: data latih, cakupan, batasan, metrik aktual, penggunaan tidak dianjurkan |
| 2 | Finalisasi `external_validation.md` + tabel pembanding Mostafa et al. |
| 3 | `NOTICE.md` lisensi pihak ketiga; dokumentasi API final |
| 4 | Latihan demo + naskah pertanyaan sulit |
| 5 | Buffer |

---

# BAGIAN I — DAFTAR KEPUTUSAN TERTUNDA

Bawa ke rapat tim. Tidak ada yang bisa diputuskan sepihak oleh pemegang BE/AI.

| # | Keputusan | Pemutus | Dampak bila tertunda |
|---|---|---|---|
| 1 | Perluasan skema response (`engine`, `model_version`, `abstained`, `disclaimer`) | Ketua Tim | Blokir Sprint 0 hari 4 |
| 2 | Adopsi kalibrasi + applicability domain **[EKSTENSI]** | Ketua Tim + Farmasi | Blokir Sprint 1 minggu 3 |
| 3 | Teks disclaimer dinamis (Bagian A.1) | Ketua Tim + Farmasi | Risiko disclaimer memuat angka tidak akurat |
| 4 | DILIrank v1 vs v2.0 **[DEVIASI]** | Tim + pembimbing | Blokir Sprint 1 minggu 1 |
| 5 | Dedup via InChIKey blok-1 (penyempurnaan §8.4) | Anggota IT + Farmasi | Blokir Sprint 1 minggu 1 |
| 6 | Ambang gerbang GNN (D.5) disepakati sebelum eksperimen | Tim | Keputusan jadi subjektif di Sprint 1 minggu 2 |

**Catatan keputusan #4.** PRD §7 dan §8.4 mengunci dataset training ke DILIrank versi Chen et al. (2016) dengan 1.036 obat. FDA telah menerbitkan DILIrank 2.0 dengan 1.336 obat — penambahan 300 obat yang disetujui 2010–2021 dan 49 obat direklasifikasi, dirujuk sebagai Olubamiwa et al., *Drug Discovery Today* 2025;30(11):104485. Distribusinya: 217 vMost-DILI-concern, 351 vLess, 414 vNo, 354 Ambiguous.

Ini peluang penguatan (data lebih banyak, anotasi lebih mutakhir), tetapi **bukan keputusan engineer**: mengubahnya berarti mengubah sitasi di proposal dan PRD. Jika diadopsi, PRD §7, §8.4, dan §15 harus direvisi bersamaan, dan fakta reklasifikasi 49 obat justru bisa dipakai sebagai bahan diskusi tentang ketidakstabilan label DILI di laporan akhir.

---

*Dokumen ini turunan HepaTwin_PRD.md v1.0 dan wajib disinkronkan ulang bila PRD direvisi.*
