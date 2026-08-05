# C12_ringkasan_jury.md — Ringkasan 1 Halaman untuk Jury Challenge

## Arsitektur

GATNN-DNN hybrid: `GATv2Conv` ×2 (atensi graf, edge-aware) + cabang DNN
(fingerprint MACCS+ECFP4+SMARTS 1200-dim) → fusion → logit. Kalibrasi Platt
post-hoc. Explainability dua tingkat: gugus (Shapley eksak, 9 pola SMARTS) +
atom (occlusion/masking, batched).

## Angka kunci (semua dari eksekusi nyata, dapat ditelusuri ke `ml/reports/`)

| | |
|---|---|
| Lingkup senyawa simulatable | 1.231 |
| Korpus training berlabel | 870 (529 positif / 341 negatif) |
| Split | train 580 / val 116 / test 174 (scaffold-disjoint, overlap=0) |
| AUC-ROC GATNN-DNN (test) | 0.7252 |
| AUC-ROC terbaik (Random Forest) | 0.7555 |
| Kalibrasi | ECE 0.1067→0.1015 (Platt, VAL 116 sampel) |
| Latensi explainability (p95, 50 molekul) | 1.38 detik |
| Test backend+ml lulus | 202/203 (1 bug pra-eksisting terdokumentasi, di luar cakupan) |

## Jawaban jujur untuk pertanyaan yang mungkin muncul

**"Kenapa pakai GNN kalau baseline (Random Forest) setara atau lebih baik?"**
Random Forest menang tipis pada dataset SEUKURAN INI (870 senyawa) — hasil
yang konsisten dengan literatur DILI-QSAR: pada dataset kecil, model
berbasis fitur tabular sering kompetitif dengan deep learning. Nilai GNN
justru pada explainability tingkat-atom yang alami untuk representasi graf
(baseline berbasis fingerprint tidak punya struktur graf untuk dijelaskan
per-atom) — trade-off yang disengaja, bukan klaim superioritas prediktif.

**"Kenapa AUC bukan 0,9?"**
Prediksi DILI dari struktur molekul saja (tanpa data farmakokinetik/klinis
pasien) secara inheren sulit — AUC 0,63–0,75 konsisten dengan literatur
DILI-QSAR published. AUC di atas 0,90 pada dataset seukuran ini justru
dicurigai kebocoran data — proyek ini punya guard otomatis untuk itu (audit
berhenti bila AUC>0,90) dan tidak pernah terpicu.

**"Dari mana zona kerusakan hati berasal — apakah itu prediksi model?"**
**Bukan.** Zona adalah lookup deterministik 1:1 dari `injury_pattern`
(LiverTox), diverifikasi tidak ada satu baris pun yang menyimpang dari
pemetaan tetap. Model AI hanya memprediksi `dili_score` (probabilitas
risiko) — zona murni data terkurasi, bukan keluaran GNN.

**"Apakah confidence/skor bisa dipercaya penuh?"**
Tidak sepenuhnya — kalibrator Platt (dipilih karena set kalibrasi kecil,
116 sampel) punya keterbatasan degenerate yang ditemukan & didokumentasikan
jujur (lihat `C12_limitations.md` §7): pada threshold 0,5, model condong
memprediksi kelas positif. AUC (ranking) tetap valid, tapi probabilitas
absolut perlu ditafsirkan hati-hati.

**"Apa risiko terbesar model ini kalau dipakai nyata?"**
336 senyawa `Ambiguous-DILI-concern` tidak pernah dipelajari model (dibuang
dari training karena tidak punya label biner sah) tapi tetap bisa dipilih
pengguna — prediksi untuk senyawa ini adalah ekstrapolasi murni, bukan
generalisasi dari data yang mirip. Ini alasan disclaimer ASME V&V 40
"decision support, bukan diagnosis" bersifat wajib, bukan formalitas.

## Keterbatasan diakui secara eksplisit (bukan disembunyikan)

Dataset kecil (~870, risiko overfitting), label dari teks FDA (bukan
pengukuran lab), kalibrator degenerate pada threshold, atribusi atom bukan
Shapley murni, 1 kegagalan test pra-eksisting di luar cakupan, latensi
request pertama pada proses baru (~8-10 detik, dimitigasi sebagian, akar
masalah belum tuntas). Rincian: `ml/reports/C12_limitations.md`.
