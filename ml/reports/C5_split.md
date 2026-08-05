# C5_split.md -- Split Dataset Training/Validasi/Testing

## 🔴 Gerbang G1 -- dua angka korpus, JANGAN disamakan

- **1231** = lingkup senyawa `is_simulatable = TRUE` (dipakai C2 featurisasi & inferensi runtime -- semua senyawa ini bisa dipilih pengguna di autocomplete dan akan mendapat skor dari model).
- **870** = korpus BERLABEL yang benar-benar dipakai training (setelah buang `Ambiguous-DILI-concern` + dedup InChIKey).

`[KEPUTUSAN AI -- PENDING REVIEW KETUA TIM]` kedua angka di atas benar dengan arti berbeda -- tidak digabung/disamakan di laporan mana pun sesuai PROJECT_FIX_MODEL.md SS4.3.

## Tabel corong (angka aktual vs ekspektasi PROJECT_FIX_MODEL.md SS4.3)

| Tahap | n aktual | Ekspektasi dokumen | Selisih |
|---|---|---|---|
| is_simulatable=TRUE dengan fingerprint valid (C2) | 1231 | 1231 | 0 |
| Buang Ambiguous-DILI-concern (label biner) | 895 | 895 | 0 |
| Tabrakan dedup (garam<->basa menyatu, n grup) | 25 | ≈25 | 0 |
| InChIKey dengan label bertentangan (G2) | 2 | 2 | 0 |
| Setelah dedup InChIKey (korpus training final) | 870 | ≈870 | 0 |
| Label positif (label_binary=1) | 529 | ≈528 | +1 |
| Label negatif (label_binary=0) | 341 | ≈342 | -1 |

Seluruh angka aktual cocok persis atau dalam selisih ±1 dari ekspektasi
dokumen sumber (selisih pos/neg ±1 wajar -- dokumen menulis "≈528/342",
bukan angka pasti). Tidak ada selisih besar yang perlu diselidiki.

## 🔴 Gerbang G2 -- InChIKey dengan label bertentangan setelah dedup

`[KEPUTUSAN AI -- PENDING REVIEW FARMASI]` ditemukan **2** InChIKey dengan label bertentangan setelah garam & basa bebas menyatu ke InChIKey standar yang sama. Default diterapkan: **label positif menang** (paling konservatif untuk alat keselamatan obat).

| InChIKey | hepatwin_id | Nama senyawa | Label (per baris) | Pemenang |
|---|---|---|---|---|
| QGZKDVFQNNGYKY-UHFFFAOYSA-N | HT0064, HT0257 | Ammonium chloride, Cisplatin | [0, 1] | 1 (positif) |
| KWTSXDURSIMDCE-UHFFFAOYSA-N | HT0067, HT0352 | Amphetamine sulfate, Dextroamphetamine sulfate | [1, 0] | 1 (positif) |

## Skema split & anti-kebocoran

- **Test (hold-out):** scaffold-disjoint, 15-20% dari korpus training, dibangun `hepatwin_ml.data.holdout.build_holdout_split` (upscale, apa adanya). **Dikunci sejak sini -- tidak disentuh sampai C7.**
- **Train/Val:** sisanya (`dev_pool`), dibagi scaffold-kfold (`hepatwin_ml.data.splits.scaffold_kfold`, k=5, fold-0 = val, sisanya = train) -- **bukan random murni**, sesuai penyimpangan yang disengaja dari teks DoD C5 (stratifikasi label diusahakan tapi scaffold-disjoint diprioritaskan bila konflik, PROJECT_FIX_MODEL.md/EXECUTION_PLAN_FIX_MODEL.md C5 langkah 4).

| Subset | n | n label positif | Proporsi positif |
|---|---|---|---|
| train | 580 | 342 | 0.5897 |
| val | 116 | 74 | 0.6379 |
| test | 174 | 113 | 0.6494 |

**Verifikasi anti-kebocoran (dieksekusi, bukan diasumsikan):**

- train vs val: InChIKey overlap=0, scaffold overlap=0
- train vs test: InChIKey overlap=0, scaffold overlap=0
- val vs test: InChIKey overlap=0, scaffold overlap=0

## Segel reproduktibilitas

Daftar lengkap InChIKey tiap subset (train/val/test) disimpan di `ml/data/interim/split_manifest.json` (di-commit, tidak di-gitignore).