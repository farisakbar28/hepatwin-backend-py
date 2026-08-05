# 09c -- Perbandingan Model Arm A (DILIrank 2.0, 839 senyawa)

Hasil nyata, 5 seed [42,43,44,45,46] x 5-fold CV, hyperparameter identik untuk
GATNN-DNN, split identik untuk ketiga model. Sumber: `09_arm_a_random_l1.json`,
`09_arm_a_scaffold_l2.json`, `09b_baselines_arm_a_random.json`,
`09b_baselines_arm_a_scaffold.json`.

## L1 -- Random 5-fold CV

| Model | AUC-ROC | AUC-PR | MCC | Brier | ECE |
|---|---|---|---|---|---|
| GATNN-DNN | 0.7385 +/- 0.0291 | 0.7976 +/- 0.0243 | 0.3521 +/- 0.0673 | 0.2285 +/- 0.0304 | 0.1776 +/- 0.0619 |
| Random Forest (ECFP4) | 0.7518 +/- 0.0362 | 0.8189 +/- 0.0345 | 0.3508 +/- 0.0590 | 0.1918 +/- 0.0097 | 0.0811 +/- 0.0186 |
| MLP (MACCS+deskriptor) | 0.6546 +/- 0.0504 | 0.7329 +/- 0.0494 | 0.2465 +/- 0.0996 | 0.2351 +/- 0.0362 | 0.1378 +/- 0.0653 |

## L2 -- Scaffold 5-fold CV (Bemis-Murcko)

| Model | AUC-ROC | AUC-PR | MCC | Brier | ECE |
|---|---|---|---|---|---|
| GATNN-DNN | 0.7336 +/- 0.0382 | 0.8017 +/- 0.0402 | 0.3406 +/- 0.0789 | 0.2416 +/- 0.0416 | 0.1948 +/- 0.0762 |
| Random Forest (ECFP4) | 0.7302 +/- 0.0470 | 0.8025 +/- 0.0497 | 0.3280 +/- 0.0712 | 0.1990 +/- 0.0138 | 0.0845 +/- 0.0234 |
| MLP (MACCS+deskriptor) | 0.6603 +/- 0.0663 | 0.7461 +/- 0.0663 | 0.2625 +/- 0.1010 | 0.2214 +/- 0.0278 | 0.1135 +/- 0.0433 |

## Konteks pembanding literatur

| Model | AUC | Skema |
|---|---|---|
| GATNN-DNN (Wibowo et al., 2025) | 0.757 | evaluasi internal, dataset 1.573 (DILIrank+LiverTox, setara Arm B) |
| **GATNN-DNN (HepaTwin, Arm A, L1)** | **0.7385** | evaluasi internal, dataset 839 (DILIrank saja, setara Arm A) |

## Kesimpulan jujur (Aturan Main #4/#5 -- tidak dikarang, tidak disembunyikan)

1. **AUC GATNN-DNN dalam band target** UPSCALE.md SS8 untuk kedua skema (L1: 0.70-0.80 -> didapat 0.7385; L2: 0.62-0.72 -> didapat **0.7336, di atas ujung atas band**, generalisasi ke scaffold baru lebih baik dari perkiraan).
2. **GNN vs tabular: hasil bercampur, bukan salah satu unggul telak.**
   - L1 (random): RF sedikit unggul (0.7518 vs 0.7385, selisih 0.0133 -- dalam 1 std kedua model, kemungkinan besar tidak signifikan)
   - L2 (scaffold): GATNN-DNN sedikit unggul (0.7336 vs 0.7302, selisih 0.0034 -- jelas tidak signifikan)
   - Pola ini **berbeda** dari temuan `dev-vedo/docs/GATE_DECISION_GNN.md` sebelumnya (GNN generik kalah telak dari LightGBM, gap 0.0535, gagal ambang unggul >=0.02). Kemungkinan penyebab: (a) GATv2Conv + edge feature lebih ekspresif dari GCN generik yang dipakai sebelumnya, (b) dataset Arm A (839) sedikit lebih besar dari dataset dev-vedo (708 train), (c) arsitektur hybrid (graf+DNN) vs GNN murni sebelumnya.
   - **Ini BUKAN pembenaran otomatis untuk memilih GNN** -- perbedaan performa terlalu kecil untuk disimpulkan sebagai "GNN menang". Kesimpulan gerbang K1 (GATNN vs tabular) tetap ditunda sampai TU.13 (Arm B, dataset lebih besar dengan LiverTox) dan tetap perlu ratifikasi manusia untuk keputusan produksi (pelajaran dari insiden `dev-vedo/docs/Decission_lead.md`).
3. **Kalibrasi mentah GATNN-DNN buruk** (ECE ~0.18-0.19, jauh lebih tinggi dari RF ~0.08) -- **mengonfirmasi kebutuhan TU.10 (kalibrasi wajib)**, konsisten dengan UPSCALE.md SS6.
4. MLP konsisten menjadi model terlemah di kedua skema -- tidak direkomendasikan sebagai kandidat produksi, dipertahankan hanya sebagai baseline pembanding sesuai spek.
