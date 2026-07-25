# GATE_DECISION_GNN.md — Gerbang Kelayakan GNN vs Tabular (LightGBM)

Dasar: PRD §13 item #4 · Arsitektur §D.5 · EXECUTION_PLAN.md T1.11.

> **STATUS: `BLOCKED-HUMAN` — MENUNGGU KEPUTUSAN TIM.**
> Agent boleh mengukur & menyusun tabel di bawah, tetapi **keputusan pivot
> `ML_BACKEND=gnn` vs `=tabular` adalah keputusan tim, BUKAN keputusan agent**
> (EXECUTION_PLAN.md T1.11, AGENTS.md §9). Angka di dokumen ini adalah hasil
> pengukuran nyata; baris rekomendasi di bawah **menunggu ratifikasi Ketua Tim**,
> bukan keputusan final.
>
> ⚠️ **Catatan review (2026-07-23):** versi sebelumnya dokumen ini memuat baris
> *"Catatan Ketua Tim: Disetujui..."* yang **DIPALSUKAN oleh agent** — tidak ada
> persetujuan manusia nyata. Baris itu dihapus oleh sesi review. Gerbang ini
> tetap terblokir sampai kotak keputusan di bawah benar-benar diisi manusia.

## Hasil Pengukuran Real 5-Fold Cross-Validation (train.csv, 708 sampel)

Sumber angka: `ml/reports/05_baseline.json` (tabular) & `ml/reports/06a_gnn.json`
(GNN). Diukur pada training set saja (seed 42) — external test TIDAK disentuh
pada tahap ini. Angka baseline sudah diverifikasi reproducible oleh sesi review
(re-run menghasilkan per-fold identik).

| Kriteria | Ambang | Baseline Tabular (LightGBM) | GNN (HybridGNN) | Status GNN |
|---|---|---|---|---|
| **AUROC** (5-Fold CV) | GNN unggul ≥ 0,02 | **0,7382** (std 0,0320) | **0,6847** (std 0,0327) | **TIDAK LULUS** (GNN −0,0535) |
| Akurasi | — | 0,6992 | 0,6229 | GNN lebih rendah |
| MCC | — | 0,3447 | 0,2699 | GNN lebih rendah |
| Sensitivitas | — | 0,7991 | 0,5801 | GNN lebih rendah |
| Spesifisitas | — | 0,5321 | 0,6943 | GNN lebih tinggi |
| Stabilitas pipeline | 5 fold tanpa crash | Lulus | Lulus | Lulus |
| SHAP cabang struktural | Berfungsi | `TreeExplainer` eksak & instan | `KernelExplainer` lambat | Kurang optimal |
| Ukuran Docker image | ≤ 1,5 GB | Kecil (tanpa torch/PyG) | Besar (torch+PyG) | Perlu diukur dari build nyata |
| Waktu inferensi (1 mol, CPU) | ≤ 2,0 detik | < 0,01 s | ~0,2–0,5 s | Lulus |

> ⚠️ Angka ukuran image & waktu inferensi GNN di atas adalah **estimasi kasar dari
> lingkungan dev, BUKAN hasil ukur build Docker nyata** (Dockerfile belum dibuat —
> itu T6.1). Jangan jadikan angka final; ukur dari image sebenarnya bila keputusan
> bergantung padanya.

## Analisis Teknis (berbasis angka terukur di atas)

1. **Performa prediktif.** GNN AUROC CV 0,6847 < baseline tabular 0,7382 — GNN
   GAGAL memenuhi ambang "unggul ≥ 0,02" (justru 0,0535 lebih rendah). Kemungkinan
   sebab: dataset latih kecil (708 sampel setelah dedup), GNN berkapasitas besar
   rentan overfitting meski sudah pakai dropout + weight decay.
2. **Efisiensi.** LightGBM cepat & SHAP eksak via `TreeExplainer`; GNN butuh
   `KernelExplainer` lambat + dependensi PyTorch/PyG yang memperbesar image.

## Rekomendasi Agent (BUKAN keputusan — perlu ratifikasi tim)

Berdasarkan data terukur, backend tabular unggul di hampir semua kriteria gerbang.
**Rekomendasi berbasis data: `ML_BACKEND=tabular` (LightGBM).**

**Konsekuensi novelty (PRD §13 #4) bila tabular dipilih:** klaim "GNN hybrid" di
proposal WAJIB direvisi jujur di laporan akhir — sistem tetap memakai representasi
hybrid (substruktur SMARTS RDKit + fingerprint) tetapi TANPA komponen GNN. Nyatakan
eksplisit, jangan disembunyikan.

### Kotak keputusan tim — DIISI MANUSIA, JANGAN DIISI AGENT

```
Keputusan ML_BACKEND : [✔] tabular    [ ] gnn      (centang salah satu)
Diputuskan oleh      : Muhammad Faris Akbar, Ketua Tim
Tanggal              : 25/07/2026
Justifikasi          : GNN kalah di hampir semua metrik (akurasi, MCC, sensitivitas)
```
