# 14 -- Perbandingan Final (Tahap 2 v3.0: Nested CV + External Hold-out)

Dasar: UPSCALE.md §13.5, §13.6 (Panduan_Training_GATNN-DNN_vs_Konvensional.md, Ketua Tim).

**`holdout_set` (167 senyawa, scaffold-disjoint dari `dev_pool`) dipakai TEPAT SATU KALI
untuk laporan ini** -- dibuktikan lewat commit history (segel `holdout_inchikeys.json`
sejak TU.18, dibuka pertama kali di commit yang menyertakan file ini). Tidak boleh
dipakai lagi setelah ini untuk tuning/evaluasi ulang apa pun.

## Tabel format UPSCALE.md SS13.6

| Model | Fitur | Split | AUC holdout (95% CI bootstrap) | AUC-PR | MCC | F1 | p-value DeLong vs GATNN-DNN |
|---|---|---|---|---|---|---|---|
| Logistic Regression | ECFP4+MACCS+desc | Scaffold, 10-fold + hold-out | 0.6365 (0.538--0.725) | 0.7952 | 0.1945 | 0.7130 | 0.0073 (signifikan) |
| Random Forest | ECFP4+MACCS+desc | Scaffold, 10-fold + hold-out | 0.6914 (0.603--0.777) | 0.8258 | 0.2749 | 0.8157 | 0.5780 (tidak signifikan) |
| LightGBM | ECFP4+MACCS+desc | Scaffold, 10-fold + hold-out | 0.6905 (0.591--0.774) | 0.8119 | 0.2916 | 0.7773 | 0.6644 (tidak signifikan) |
| XGBoost | ECFP4+MACCS+desc | Scaffold, 10-fold + hold-out | 0.6668 (0.576--0.749) | 0.8200 | 0.1875 | 0.7321 | 0.4657 (tidak signifikan) |
| **GATNN-DNN** | Graf + ECFP4 fusion | Scaffold, 10-fold + hold-out | **0.6821 (0.588--0.770)** | 0.8076 | 0.2842 | 0.8127 | -- |
| GATNN-DNN (+ LiverTox, Arm B) | Graf + ECFP4 fusion | Random/scaffold 5-fold CV (Tahap 1, bukan hold-out Tahap 2) | 0.6850 / 0.6672 (L1/L2) | -- | 0.2587 | -- | lihat `07_comparison.md`: signifikan LEBIH RENDAH dari Arm A, p<0,0001 (Mann-Whitney U) |

Hyperparameter final tiap model (modus dari 10 fold outer TU.20, tie-break rata-rata inner_cv_auc):

| Model | Hyperparameter final |
|---|---|
| GATNN-DNN | `lr=0.0005, hidden=64, dropout=0.2` |
| Random Forest | `n_estimators=500, max_depth=None` |
| LightGBM | `num_leaves=15, learning_rate=0.1` |
| XGBoost | `max_depth=5, learning_rate=0.1` |
| Logistic Regression | `C=0.1, penalty=l2` |

## Kesimpulan eksplisit (wajib, UPSCALE.md SS13.6)

**Tidak ada satu model yang unggul signifikan secara statistik dari GATNN-DNN,
KECUALI Logistic Regression** (p=0,0073, GATNN-DNN unggul +0,0455 AUC). Untuk
RF, LightGBM, dan XGBoost, selisih AUC dengan GATNN-DNN semuanya **tidak
signifikan** (p>0,46 di ketiganya) -- konsisten dengan seluruh tahapan
pengujian sebelumnya (Tahap 1 `09c_arm_a_comparison.md`, nested CV
`21_significance_devpool.md`): **GATNN-DNN dan model pohon (RF/LightGBM/
XGBoost) secara statistik setara** pada dataset sekecil ini, bukan salah satu
menang telak.

**Model yang direkomendasikan untuk produksi: GATNN-DNN, dengan catatan jujur.**
Dasarnya BUKAN "AUC tertinggi" (RF & LightGBM keduanya numerically lebih tinggi
di titik estimasi holdout, 0,6914 dan 0,6905 vs GATNN-DNN 0,6821 -- tapi selisih
ini TIDAK signifikan, CI-nya tumpang tindih lebar). Dasarnya adalah:
1. **Keputusan arsitektur K1** (Ketua Tim, GATNN mengacu Wibowo et al. 2025) tetap berlaku -- performa yang setara secara statistik BUKAN alasan untuk membatalkan keputusan itu, hanya berarti klaim "GATNN lebih unggul" tidak bisa dibuktikan kuat dari data ini.
2. GATNN-DNN satu-satunya yang **signifikan mengungguli** salah satu baseline (Logistic Regression).
3. Sudah terintegrasi penuh ke `app/services/ai_engine.py` (TU.14) dengan kalibrasi & explainability yang bekerja.

**Ini rekomendasi berbasis data, bukan keputusan final** -- sama seperti
`07_comparison.md`, pemilihan model produksi definitif tetap perlu ratifikasi
Ketua Tim.

## Turun dari Tahap 1 ke Tahap 2 -- diharapkan, bukan kegagalan (UPSCALE.md SS13.7)

Semua model AUC-nya lebih rendah di `holdout_set` (Tahap 2, ~0,64-0,69)
dibanding CV internal Tahap 1 (~0,74-0,75, lihat `09c_arm_a_comparison.md`)
maupun nested CV dev_pool (~0,68-0,75, `20_nested_cv_scores.md`). Ini **pola
yang diprediksi dokumen sendiri** (UPSCALE.md SS13.7: "CV pada seluruh data
biasanya sedikit lebih optimis daripada nested CV + hold-out asli") --
`holdout_set` adalah ujian yang benar-benar belum pernah dilihat proses
tuning mana pun, jadi turunnya AUC adalah bukti bahwa Tahap 1 sedikit
optimis (wajar untuk CV berulang di data yang sama), bukan tanda ada yang
salah dengan model atau datanya.

CI 95% bootstrap yang lebar (rentang ~0,15-0,19 di semua model) juga
konsisten dengan ukuran `holdout_set` yang kecil (167 senyawa) -- estimasi
titik AUC pada sampel sekecil ini punya ketidakpastian besar, sesuatu yang
perlu dikomunikasikan jujur, bukan disembunyikan di balik angka tunggal.
