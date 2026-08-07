# F2 -- Temuan Tambahan: Keterjangkauan LOW_EXPOSURE

Ditemukan saat menjalankan uji senyawa acuan F2 (`scripts/derive_thresholds.py`): senyawa `vNo-DILI-concern` dengan skor AI terendah katalog (AI_LOW di ketiga kandidat T_low/T_high) tetap **MERAH** pada skenario dosis wajar -- bukan karena band AI, melainkan karena `exposure_category` selalu HIGH_EXPOSURE.

## Sweep kovariat pasien realistis (n=20250)

Rentang: usia 18-90 (step 3), tinggi 150-190cm, BMI 16-40 (berat diturunkan dari BMI x tinggi², dibatasi 30-250kg), kedua jenis kelamin, dosis relatif 0.5-50 mg/kg.

| exposure_category | Jumlah | Persentase |
|---|---|---|
| LOW_EXPOSURE | 0 | 0.00% |
| MODERATE_EXPOSURE | 2602 | 12.85% |
| HIGH_EXPOSURE | 17648 | 87.15% |

- `cmax_auc_ratio` minimum yang tercapai di seluruh sweep: **0.3132** pada (usia,tinggi,BMI,berat,jk,dosis/kg) = (90, 190, 40, 144.4, 'L', 0.5)
- `cmax_auc_ratio` maksimum: **0.4905** pada (18, 150, 16, 36.0, 'L', 0.5)
- Ambang `moderate_threshold` yang harus dilewati agar LOW: **0.30** (non-vulnerable) / **0.20** (vulnerable, usia>=60 atau BMI>=30)

## Akar sebab (diverifikasi lewat kode, bukan dugaan)

`app/services/pbpk_engine.py` `_simulate_base()` menyelesaikan ODE linear untuk **dosis basis 1.0 mg**, lalu `simulate()` mengalikan seluruh kurva konsentrasi (`sol_y_base * dosis_mg`) secara linear. Karena `cmax_hati = max(C_L(t))` dan `auc_hati = trapz(C_L(t))` SAMA-SAMA diskalakan linear oleh `dosis_mg` yang sama, rasio `cmax/auc` **matematis tidak bergantung pada dosis sama sekali** -- hanya pada parameter alometrik pasien (usia, jenis kelamin, berat, tinggi). Ini diverifikasi langsung: rasio untuk satu profil pasien tetap **persis sama** (0.441640) pada dosis 50mg, 200mg, 500mg, 1000mg, dan 4000mg.

Konsekuensinya: kondisi `cmax_auc_ratio > moderate_threshold` pada `exposure_evaluator.py` TIDAK PERNAH bisa diselamatkan oleh dosis rendah (`dose_per_kg < 10`) selama rasio pasien itu sendiri sudah di atas ambang -- dan dari sweep 20.250 kombinasi realistis di atas, **rasio SELALU di atas 0.30** (minimum terukur 0.3132, jauh di atas ambang non-vulnerable). Pola ini **identik secara struktural** dengan temuan SS3.1 PROJECT_FUSION.md (rantai `or` yang membuat satu kondisi selalu menang) -- hanya saja terjadi di `exposure_evaluator.py`, bukan `fusion_service.py`, dan bukan pada `dili_score` tapi pada `cmax_auc_ratio`.

## Implikasi untuk cakupan branch `fusion`

- Matriks 3x3 (F3, PROJECT_FUSION.md SS4.1) memetakan `(AI_LOW, EXP_LOW) -> HIJAU`. Bila `EXP_LOW` PRAKTIS TIDAK TERJANGKAU untuk kovariat pasien realistis manapun (terlepas dari kandidat T_low/T_high AI mana yang dipilih di F2), maka **HIJAU akan tetap kode mati** setelah F3 -- DoD proyek "Hijau terbukti bisa muncul" TIDAK akan terpenuhi lewat skenario pasien realistis, walau AI band-nya sendiri sudah benar (AI_LOW tercapai untuk banyak senyawa vNo).
- Ini BUKAN sesuatu yang bisa diperbaiki di lapisan fusi (F3) -- akar masalahnya ada di `exposure_evaluator.py` (enam ambang `30.0/10.0/0.40/0.35/0.30/0.20`), yang menurut `PROJECT_FUSION.md` SS5 & gerbang K3 **berada di luar wewenang agen untuk diubah** tanpa keputusan Farmasi eksplisit. F5 (audit exposure_evaluator) SUDAH mencakup analisis sensitivitas serupa (langkah 4) -- temuan ini MENDAHULUI F5 secara organik karena ditemukan saat membangun uji acuan F2, dan sebaiknya jadi INPUT UTAMA diskusi K3 dengan Farmasi, bukan ditunda sampai F5/F9.
- Mitigasi yang TERSEDIA tanpa mengubah `exposure_evaluator.py`: matriks F3 tetap diimplementasikan sesuai rancangan (PRD-setia, K1 disetujui default), dan HIJAU dibuktikan LULUS lewat **unit test AI-axis-only** (AI_LOW x EXP_LOW disuntik langsung sebagai sel matriks, TIDAK lewat pipeline PBPK penuh) -- ini membuktikan matriksnya BENAR secara struktural (§3.1/§3.2 AI-axis sudah diperbaiki), tapi HARUS dinyatakan eksplisit di F9 bahwa HIJAU end-to-end lewat skenario pasien nyata belum tercapai selama enam ambang exposure belum direvisi Farmasi. Kejujuran ini WAJIB masuk `reports/F9_limitations_fusion.md`.

## Contoh kombinasi yang mencapai LOW_EXPOSURE

**TIDAK ADA** -- nol dari 20250 kombinasi realistis yang diuji mencapai LOW_EXPOSURE.

