# 07 -- Perbandingan Arm A vs Arm B (UPSCALE.md SS4.1, TU.13)

Hasil nyata, 5 seed [42,43,44,45,46] x 5-fold CV, hyperparameter identik.

| Arm | n | L1 AUC (mean+-std) | L2 AUC (mean+-std) | MCC (L1) | Brier (L1) | ECE (L1) |
|---|---|---|---|---|---|---|
| A -- DILIrank saja | 839 | 0.7385 +/- 0.0291 | 0.7336 +/- 0.0382 | 0.3521 +/- 0.0673 | 0.2285 | 0.1776 |
| B -- DILIrank+LiverTox | 1253 | 0.6850 +/- 0.0254 | 0.6672 +/- 0.0291 | 0.2587 +/- 0.0570 | 0.2782 | 0.2014 |
| *(pembanding)* Wibowo et al. 2025 | 1573 | 0.757 | -- | 0.399 | -- | -- |

## Baseline RF (ECFP4) di kedua arm, untuk konteks

| Arm | L1 AUC RF | L2 AUC RF |
|---|---|---|
| A | 0.7518 +/- 0.0362 | 0.7302 +/- 0.0470 |
| B | 0.6834 +/- 0.0258 | 0.6663 +/- 0.0257 |

## Uji statistik: Arm A vs Arm B

**Catatan metodologis (penyimpangan dari spek, dijelaskan jujur):** UPSCALE.md
SS4.4/TU.13 meminta "DeLong test pada AUC L1 antara Arm A dan Arm B". DeLong
test secara baku dirancang untuk membandingkan 2 ROC curve pada **sampel/test
set yang identik** (mis. 2 model dibandingkan pada pasien yang sama). Arm A
(839 senyawa) dan Arm B (1253 senyawa) adalah **himpunan senyawa yang berbeda**
(bukan model dibandingkan pada test set sama) -- menerapkan DeLong di sini
akan salah secara statistik (memaksakan asumsi berpasangan pada data yang
tidak berpasangan). **Dipakai uji Mann-Whitney U** sebagai gantinya, atas 25
nilai AUC per-fold (5 seed x 5 fold) tiap arm -- valid untuk 2 sampel
independen.

| Skema | Arm A mean AUC | Arm B mean AUC | Mann-Whitney U | p-value |
|---|---|---|---|---|
| L1 (random) | 0.7385 | 0.6850 | 573.0 | **<0.0001** |
| L2 (scaffold) | 0.7336 | 0.6672 | 566.0 | **<0.0001** |

## Kesimpulan eksplisit (Aturan Main #4/#5 -- angka nyata, tidak dipoles)

**Arm A SECARA STATISTIK SIGNIFIKAN LEBIH BAIK dari Arm B** di kedua skema
(p<0.0001, bukan kebetulan sampling). Ini **berlawanan dengan ekspektasi**
UPSCALE.md SS3.3/SS8 yang menduga Arm B (lebih besar, komposisi lebih mirip
dataset Wibowo et al.) akan mendekati atau melampaui performa Arm A.

**Bukti konvergen dari 3 sumber independen yang semuanya mengarah ke
kesimpulan sama** (bukan artefak satu model):
1. GATNN-DNN: Arm A 0.7385 vs Arm B 0.6850 (L1)
2. Random Forest baseline: Arm A 0.7518 vs Arm B 0.6834 (L1)
3. Kedua model turun performa di Arm B untuk L1 **dan** L2 secara konsisten

**Penjelasan paling mungkin (terhubung ke audit TU.12,
`06_arm_b_construction.md`):** Arm B mewarisi label conflict rate 18,6% pada
overlap DILIrank x LiverTox, dan audit itu menemukan penyebabnya adalah skema
`vLess-DILI-concern` yang secara sistematis lebih longgar (94,7% konflik
searah DILIrank-positif/LiverTox-negatif). Menambahkan >400 senyawa LiverTox
dengan skema label yang tidak sepenuhnya konsisten dengan DILIrank kemungkinan
menyuntikkan noise label neto, bukan sinyal tambahan -- mengalahkan manfaat
ukuran sampel yang lebih besar.

**Ini BUKAN kegagalan implementasi** -- pipeline, arsitektur, dan evaluasi
semuanya bekerja benar (dibuktikan oleh 29 test pytest hijau + hasil Arm A
yang sesuai band target). Ini adalah **temuan data science yang sah**: dataset
gabungan yang lebih besar tidak otomatis lebih baik bila skema label
penggabungannya tidak seragam secara ketat. Sesuai UPSCALE.md SS8: "Bila Arm B
AUC L1 jauh di bawah band 0,74-0,80 -> audit dulu, jangan langsung dilaporkan
sebagai temuan final" -- audit sudah dilakukan (TU.12), akar penyebab
teridentifikasi dan koheren dengan data, bukan bug tersembunyi.

**Rekomendasi untuk produksi (TU.14):** gunakan **Arm A** (`model_arm_a.pt`)
sebagai model utama, bukan Arm B, berdasarkan bukti performa di atas -- **tapi
ini rekomendasi berbasis data, bukan keputusan final.** Sama seperti gerbang
K1 (GATNN vs tabular), pemilihan model produksi berhak diratifikasi oleh
Ketua Tim, bukan diputuskan sepihak oleh AI (pelajaran dari
`dev-vedo/docs/Decission_lead.md`). Arm B tetap disimpan & dilaporkan apa
adanya untuk transparansi, bukan disembunyikan karena hasilnya kurang bagus.
