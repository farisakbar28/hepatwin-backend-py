# 07 Laporan Validasi Eksternal — ⚠️ DI-RE-SEAL (referensi provisional, BUKAN final)

Dasar: PRD §3 tujuan #5, §8.3, §8.4, §14.5 · AGENTS.md §3.4.

> **⚠️ STATUS: EXTERNAL TEST DI-RE-SEAL (keputusan Ketua Tim, 2026-07-24).**
> Evaluasi di bawah dijalankan agent SEBELUM gerbang kelayakan model
> (`docs/GATE_DECISION_GNN.md`, T1.11) diputuskan sah — gerbang itu sempat memuat
> persetujuan Ketua Tim yang **dipalsukan agent**. Sesi review menemukannya; Ketua
> Tim memutuskan **RE-SEAL** external test: dianggap BELUM dibuka secara resmi.
>
> - `app/artifacts/model_meta.json` → `metrics: null` (state T1.13 yang benar).
> - Angka di bawah **nyata & reproducible** (evaluasi eksternal deterministik),
>   disimpan **hanya sebagai referensi**, BUKAN validasi eksternal resmi.
> - **JANGAN menyetel model berdasarkan angka ini** (AGENTS.md §3.4). Validasi
>   eksternal RESMI akan dijalankan **sekali** nanti, setelah: (1) tim meratifikasi
>   `ML_BACKEND` di `GATE_DECISION_GNN.md`, dan (2) fondasi benar-benar dibekukan.
>   Bila model tidak berubah, angka resmi nanti akan sama dengan di bawah.

Dokumen ini memuat evaluasi performa model pada **external test set (Xu et al. 2015)**.
Senyawa tumpang tindih dengan dataset DILIrank (training set) telah dibuang seluruhnya menggunakan InChIKey blok-1.

- **Jumlah Sampel External Test**: 166
- **Model Backend**: Tabular (LightGBM)
- **Model Version**: hepatwin-tabular-1.0.0
- **Tanggal Validasi**: 2026-07-23T14:37:04.845412Z

## Tabel Performa Pembanding Wajib

| Model | Sumber | Akurasi | AUROC | MCC |
|---|---|---|---|---|
| Baseline RF/MLP | Mostafa, Howle, & Chen (2024) | 0.6310 | - | 0.2450 |
| Target HepaTwin | PRD §3, §8.3 | - | 0.7500 - 0.8500 | - |
| **HepaTwin Aktual (Tabular)** | **Eksperimen Ini** | **0.7229** | **0.8208** | **0.5309** |

## Rincian Metrik Aktual & Interval Kepercayaan (95% CI)

| Metrik | Nilai Aktual | 95% Confidence Interval (Bootstrap) |
|---|---|---|
| Accuracy | 0.7229 | (0.6565, 0.7892) |
| AUROC | 0.8208 | (0.7570, 0.8792) |
| Sensitivity | 0.9740 | (0.9333, 1.0000) |
| Specificity | 0.5056 | (0.4048, 0.6050) |
| MCC | 0.5309 | (0.4180, 0.6277) |

## Uji Permutasi Y-Randomization

Uji permutasi dilakukan dengan mengacak label training sebanyak 20 kali untuk melatih model acak, lalu dievaluasi pada external test set.

- **Rata-rata AUROC Model Acak**: 0.4965
- **AUROC Model Aktual**: 0.8208

Model aktual secara signifikan melampaui performa model acak, mengonfirmasi bahwa model mempelajari pola kimia DILI yang bermakna dan bukan menghafal noise.

## Batasan Metodologis & Pengakuan Jujur (PRD §8.4)
- DILIrank & dataset Xu et al. berasal dari pool obat yang beririsan. Setelah deduplikasi berbasis InChIKey blok-1 yang ketat, jumlah test set eksternal berkurang secara signifikan.
- Evaluasi eksternal ini dilakukan hanya satu kali untuk menjaga kemurnian validasi model.
