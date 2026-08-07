# R3 -- Uji Ulang Senyawa Acuan & Distribusi Warna End-to-End (gerbang G4)

Seluruh hasil di bawah lewat PIPELINE PENUH (AI dili_score cache F1 + PBPK v2.3 SUNGGUHAN dgn XLogP senyawa asli + exposure_evaluator v2.3 SUNGGUHAN + FusionService), BUKAN unit test injeksi sel matriks. `T_LOW`/`T_HIGH` tidak dihitung ulang -- hanya diuji ulang.

## Uji senyawa acuan

| Kandidat | Acetaminophen (10.500mg/70kg/45th/L, PRD v2.3 Skenario A) | Calcitonin salmon vNo (300mg/60kg/28th/P, dosis wajar) |
|---|---|---|
| (a) Tersier | **RED** (AI_MID x HIGH_EXPOSURE, exposure_index=14.86) -- LULUS | **GREEN** (AI_LOW x LOW_EXPOSURE, exposure_index=8.09) -- LULUS |
| (b) Pemetaan-balik | **RED** (AI_MID x HIGH_EXPOSURE, exposure_index=14.86) -- LULUS | **GREEN** (AI_LOW x LOW_EXPOSURE, exposure_index=8.09) -- LULUS |
| (c) Biaya klinis | **RED** (AI_MID x HIGH_EXPOSURE, exposure_index=14.86) -- LULUS | **GREEN** (AI_LOW x LOW_EXPOSURE, exposure_index=8.09) -- LULUS |

✅ **HIJAU tercapai lewat pipeline penuh** untuk setidaknya satu kandidat -- menutup celah yang tersisa di siklus v2.1 (dulu hanya terbukti struktural lewat unit test).

## Distribusi warna atas katalog 1.231 senyawa (per kandidat, profil dewasa sehat dosis wajar)

| Kandidat | HIJAU | KUNING | MERAH |
|---|---|---|---|
| (a) Tersier | 96 (7.8%) | 911 (74.0%) | 224 (18.2%) |
| (b) Pemetaan-balik | 96 (7.8%) | 911 (74.0%) | 224 (18.2%) |
| (c) Biaya klinis | 96 (7.8%) | 911 (74.0%) | 224 (18.2%) |

## Variasi warna terhadap profil pasien (metode b, T_low=0.5458/T_high=0.6866)

| Senyawa | Dewasa sehat, dosis rendah | Dewasa, dosis tinggi | Lansia | BMI tinggi |
|---|---|---|---|---|
| Abacavir sulfate | YELLOW | RED | YELLOW | YELLOW |
| Aztreonam | RED | RED | RED | RED |
| Cefuroxime sodium | RED | RED | RED | RED |
| Demeclocycline hydrochloride | YELLOW | RED | YELLOW | YELLOW |
| Eribulin mesylate | YELLOW | RED | YELLOW | YELLOW |
| Gadobenate dimeglumine | YELLOW | RED | YELLOW | YELLOW |
| Lactitol | GREEN | RED | YELLOW | YELLOW |
| Methotrexate sodium | YELLOW | RED | YELLOW | YELLOW |
| Octreotide acetate | GREEN | RED | YELLOW | YELLOW |
| Ponesimod | YELLOW | RED | YELLOW | YELLOW |
| Selegiline hydrochloride | YELLOW | RED | YELLOW | YELLOW |
| Tigecycline | YELLOW | RED | YELLOW | YELLOW |

**10/12 senyawa contoh berubah warna tergantung profil pasien** -- membuktikan kovariat pasien kini benar-benar memengaruhi hasil visual (memperbaiki keluhan "personalisasi tidak terasa" dari fase sebelumnya, karena exposure_index kini dipengaruhi dosis+fisiologi+XLogP senyawa, bukan rasio yang selalu sama).

## Gerbang G4 -- pilih T_LOW/T_HIGH final

Default: **metode (b) pemetaan-balik (T_low=0.5458, T_high=0.6866)**, konsisten dgn default gerbang K2 siklus v2.1 -- `dili_score` tidak berubah, sehingga alasan pemilihan sebelumnya (mempertahankan maksud desain PRD awal) tetap berlaku. `[KEPUTUSAN AI -- PENDING REVIEW FARMASI + KETUA TIM, gerbang G4]`

