# F2 -- Penurunan Ambang T_low / T_high dari Data

Berbasis `reports/F1_scores_catalogue.csv` (n=1231).

> \U0001F6A9 **TEMUAN KRITIS BARU, ditemukan saat menjalankan uji senyawa acuan di bawah:** kandidat
> senyawa aman (Calcitonin salmon, AI_LOW di ketiga metode) TIDAK mencapai HIJAU pada skenario dosis
> wajar manapun -- bukan karena pemilihan T_low/T_high AI, tapi karena `exposure_category` dari
> `exposure_evaluator.py` SELALU HIGH_EXPOSURE untuk kovariat pasien realistis (0 dari 20.250 kombinasi
> yang disweep mencapai LOW_EXPOSURE). Detail lengkap, akar sebab, dan implikasinya ada di
> **`reports/F2_exposure_reachability_finding.md`**. Ini BUKAN sesuatu yang bisa diperbaiki di F2/F3
> (lapisan fusi) -- akar masalahnya di `exposure_evaluator.py`, di luar wewenang agen tanpa keputusan
> Farmasi (gerbang K3). Dampaknya: DoD "Hijau terbukti bisa muncul" TIDAK akan tercapai lewat skenario
> pasien end-to-end sampai K3 diputuskan, walau band AI (dili_score) itu sendiri sudah diperbaiki.

## Ringkasan tiga kandidat

| Metode | T_low | T_high |
|---|---|---|
| (a) Tersier | 0.6046 | 0.6664 |
| (b) Pemetaan-balik | 0.5458 | 0.6866 |
| (c) Biaya klinis | 0.5621 | 0.6898 |

**Catatan metode (c):** dokumen (`PROJECT_FUSION.md` SS4.2) hanya menspesifikasikan kriteria T_low (persentil-5 gabungan vMost+vLess, false negative rate <=5%). T_high metode (c) di atas adalah **interpretasi AI** -- persentil-95 distribusi vNo, kriteria simetris (false positive rate <=5% utk label MERAH pada senyawa vNo). `[KEPUTUSAN AI -- PENDING REVIEW FARMASI]`

## Kandidat (a) Tersier (T_low=0.6046, T_high=0.6664)

**Distribusi warna (AI-band murni, seluruh katalog):**

| Warna | Jumlah | Persentase |
|---|---|---|
| HIJAU | 406 | 32.98% |
| KUNING | 419 | 34.04% |
| MERAH | 406 | 32.98% |

**Distribusi warna per dili_concern:**

| dili_concern | HIJAU | KUNING | MERAH | n |
|---|---|---|---|---|
| Ambiguous-DILI-concern | 94 (28.0%) | 127 (37.8%) | 115 (34.2%) | 336 |
| vLess-DILI-concern | 65 (19.6%) | 130 (39.2%) | 137 (41.3%) | 332 |
| vMost-DILI-concern | 24 (11.7%) | 69 (33.5%) | 113 (54.9%) | 206 |
| vNo-DILI-concern | 223 (62.5%) | 93 (26.1%) | 41 (11.5%) | 357 |

**Sensitivity/specificity pada T_low=0.6046** (biner: positif=vMost+vLess, negatif=vNo, 336 senyawa Ambiguous-DILI-concern dikecualikan, n=895):

- Sensitivity (recall vMost+vLess): **83.46%**
- Specificity (recall vNo): **62.46%**

**Uji senyawa acuan (pipeline PBPK + exposure + matriks kandidat):**

- Acetaminophen (HT0012, dili_score=0.6501, AI_MID) x overdosis 4000mg/70kg/40th (HIGH_EXPOSURE, dose_per_kg=57.14, cmax_auc_ratio=0.4359) -> **MERAH** (harapan: MERAH -- LULUS)
- Calcitonin salmon (HT0178, vNo, dili_score=0.5078, AI_LOW) x dosis wajar 200mg/65kg/30th (HIGH_EXPOSURE, dose_per_kg=3.08, cmax_auc_ratio=0.4416) -> **MERAH** (harapan: HIJAU tercapai -- GAGAL)

## Kandidat (b) Pemetaan-balik (T_low=0.5458, T_high=0.6866)

**Distribusi warna (AI-band murni, seluruh katalog):**

| Warna | Jumlah | Persentase |
|---|---|---|
| HIJAU | 96 | 7.80% |
| KUNING | 913 | 74.17% |
| MERAH | 222 | 18.03% |

**Distribusi warna per dili_concern:**

| dili_concern | HIJAU | KUNING | MERAH | n |
|---|---|---|---|---|
| Ambiguous-DILI-concern | 15 (4.5%) | 257 (76.5%) | 64 (19.0%) | 336 |
| vLess-DILI-concern | 12 (3.6%) | 238 (71.7%) | 82 (24.7%) | 332 |
| vMost-DILI-concern | 1 (0.5%) | 151 (73.3%) | 54 (26.2%) | 206 |
| vNo-DILI-concern | 68 (19.0%) | 267 (74.8%) | 22 (6.2%) | 357 |

**Sensitivity/specificity pada T_low=0.5458** (biner: positif=vMost+vLess, negatif=vNo, 336 senyawa Ambiguous-DILI-concern dikecualikan, n=895):

- Sensitivity (recall vMost+vLess): **97.58%**
- Specificity (recall vNo): **19.05%**

**Uji senyawa acuan (pipeline PBPK + exposure + matriks kandidat):**

- Acetaminophen (HT0012, dili_score=0.6501, AI_MID) x overdosis 4000mg/70kg/40th (HIGH_EXPOSURE, dose_per_kg=57.14, cmax_auc_ratio=0.4359) -> **MERAH** (harapan: MERAH -- LULUS)
- Calcitonin salmon (HT0178, vNo, dili_score=0.5078, AI_LOW) x dosis wajar 200mg/65kg/30th (HIGH_EXPOSURE, dose_per_kg=3.08, cmax_auc_ratio=0.4416) -> **MERAH** (harapan: HIJAU tercapai -- GAGAL)

## Kandidat (c) Biaya klinis (T_low=0.5621, T_high=0.6898)

**Distribusi warna (AI-band murni, seluruh katalog):**

| Warna | Jumlah | Persentase |
|---|---|---|
| HIJAU | 178 | 14.46% |
| KUNING | 853 | 69.29% |
| MERAH | 200 | 16.25% |

**Distribusi warna per dili_concern:**

| dili_concern | HIJAU | KUNING | MERAH | n |
|---|---|---|---|---|
| Ambiguous-DILI-concern | 39 (11.6%) | 239 (71.1%) | 58 (17.3%) | 336 |
| vLess-DILI-concern | 19 (5.7%) | 239 (72.0%) | 74 (22.3%) | 332 |
| vMost-DILI-concern | 8 (3.9%) | 148 (71.8%) | 50 (24.3%) | 206 |
| vNo-DILI-concern | 112 (31.4%) | 227 (63.6%) | 18 (5.0%) | 357 |

**Sensitivity/specificity pada T_low=0.5621** (biner: positif=vMost+vLess, negatif=vNo, 336 senyawa Ambiguous-DILI-concern dikecualikan, n=895):

- Sensitivity (recall vMost+vLess): **94.98%**
- Specificity (recall vNo): **31.37%**

**Uji senyawa acuan (pipeline PBPK + exposure + matriks kandidat):**

- Acetaminophen (HT0012, dili_score=0.6501, AI_MID) x overdosis 4000mg/70kg/40th (HIGH_EXPOSURE, dose_per_kg=57.14, cmax_auc_ratio=0.4359) -> **MERAH** (harapan: MERAH -- LULUS)
- Calcitonin salmon (HT0178, vNo, dili_score=0.5078, AI_LOW) x dosis wajar 200mg/65kg/30th (HIGH_EXPOSURE, dose_per_kg=3.08, cmax_auc_ratio=0.4416) -> **MERAH** (harapan: HIJAU tercapai -- GAGAL)

