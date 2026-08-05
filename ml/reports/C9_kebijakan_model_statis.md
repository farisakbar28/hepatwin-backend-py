# C9_kebijakan_model_statis.md — Pembekuan Model untuk Deployment

## Kebijakan: model statis, BUKAN continuous learning

C9 (Dokumen Kerja Internal) melarang eksplisit *continuous learning* /
*auto-retraining* di runtime. HepaTwin memakai **satu snapshot bobot model
beku**, dilatih offline (C6), dievaluasi sekali (C7), lalu dibekukan sebagai
artefak statis yang dimuat ulang identik di setiap proses backend.

### Alasan

1. **Mencegah *model drift* tak terkendali.** Model yang belajar dari
   traffic produksi tanpa kurasi bisa perlahan bergeser dari distribusi
   data yang divalidasi (DILIrank 2.0 + LiverTox), tanpa evaluasi ulang
   yang setara dengan C7 (hold-out, kalibrasi, baseline pembanding).
2. **Mencegah *data poisoning*.** Tanpa continuous learning, tidak ada
   jalur bagi input pengguna (bahkan yang salah/adversarial) untuk mengubah
   bobot model — permukaan serangan ini tertutup by design, bukan hanya
   oleh kebijakan operasional.
3. **Reproduktibilitas ilmiah (ASME V&V 40).** Skor `dili_score` untuk
   senyawa yang sama harus identik di request manapun, kapanpun — ini
   prasyarat literal untuk audit juri dan validasi V&V yang menuntut hasil
   deterministik, bukan model yang terus berubah.
4. **Database tertutup.** Karena korpus simulasi dibatasi 1.231 senyawa
   `is_simulatable = TRUE` (Keputusan Desain Final), tidak ada mekanisme
   pengguna memasukkan data training baru — continuous learning tidak
   punya sumber data yang sah untuk dipelajari bahkan bila diaktifkan.

## Implementasi kebijakan di kode runtime (`app/`)

| Aturan | Bukti |
|---|---|
| `model.eval()` dipanggil setelah load | `app/services/ai_engine.py` (C10) — dipanggil sekali di `__init__`, model tidak pernah dikembalikan ke `.train()` mode |
| Seluruh inferensi dibungkus `torch.no_grad()` | `app/services/ai_engine.py` (C10) — setiap forward pass (`predict_dili_risk`, `get_explainability`) di dalam context manager `torch.no_grad()` |
| Tidak ada `.backward()` / `optimizer.step()` di `app/` | Diverifikasi lewat pencarian kode (`ml/tests/test_static_model_policy.py`) — nol kecocokan di seluruh `app/` |
| Tidak ada penulisan ulang file bobot saat runtime | Tidak ada `torch.save(...)` di jalur `app/` manapun — model hanya ditulis offline oleh `ml/scripts/run_train.py`, dibaca (bukan ditulis) oleh `app/` |

## Cara memperbarui model secara sengaja (proses manual + review)

Continuous learning otomatis dilarang, tapi model **bisa** diperbarui lewat
proses manual bila ada alasan sah (data DILIrank/LiverTox baru, bug
featurization diperbaiki, dst.):

1. Jalankan ulang pipeline offline dari awal: `ml/scripts/run_featurization.py`
   (C2) → `run_split.py` (C5) → `run_train.py` (C6) → `run_evaluate.py` (C7).
2. Bandingkan metrik hold-out baru vs `ml/reports/C7_evaluasi.md` versi
   sebelumnya — model baru **tidak boleh** menggantikan yang lama tanpa
   evaluasi yang setara atau lebih baik, didokumentasikan di PR/commit.
3. Review manusia (bukan otomatis) wajib menyetujui perubahan sebelum
   `ml/scripts/export_to_app.py` (C9) dijalankan untuk menimpa artefak di
   `app/models/`.
4. Commit terpisah, pesan jelas menyebut alasan pembaruan (bukan retraining
   rutin terjadwal).

**Tidak ada** cron job, webhook, atau trigger otomatis apa pun yang
memanggil skrip training dari kode `app/` — seluruh pipeline `ml/` hanya
dijalankan manual oleh manusia.

## Artefak yang dibekukan

| File | Sumber | Isi |
|---|---|---|
| `app/models/model_gatnn_dnn.pt` | `ml/scripts/run_train.py` (C6), seed=42 | State dict `GatnnDnn` |
| `app/models/calibrator_gatnn_dnn.pkl` | `ml/scripts/run_evaluate.py` (C7) | Kalibrator Platt (VAL, <200 sampel) |
| `app/models/model_gatnn_dnn_metadata.json` | `ml/scripts/run_train.py` (C6) | Hyperparameter, seed, n_train, tanggal, hash `split_manifest.json`, metrik val |

Disalin lewat `ml/scripts/export_to_app.py` (C9) — penyalinan terkontrol
lewat skrip, bukan manual, dan **tidak menimpa** artefak lama karena nama
file baru (`model_gatnn_dnn.pt`, bukan `model.pt`) sengaja berbeda dari
konvensi lama supaya kedua model bisa dibandingkan bila diperlukan.

`app/core/config.py`: `AI_MODEL_PATH` default diubah dari
`"models/model.pt"` (path relatif-ke-cwd yang secara diam-diam TIDAK
pernah cocok dengan direktori nyata `app/models/` — bug pra-eksisting yang
ikut diperbaiki di sini) menjadi `"app/models/model_gatnn_dnn.pt"`, konsisten
dengan `Procfile` (`uvicorn app.main:app` dijalankan dari root repo).
