# F9 -- Batasan & Keterbatasan Branch `fusion` (D7 & D9)

Dokumen ini WAJIB dibaca sebelum mengklaim branch `fusion` "selesai" ke Ketua Tim, Farmasi, atau juri.
Kejujuran di sini diprioritaskan di atas kesan sempurna.

---

## 1. Temuan SS3.1 (hijau tidak pernah muncul) -- diperbaiki di lapisan fusi, BUKAN di kalibrasi

Kalibrator produksi (`calibrator_gatnn_dnn.pkl`, Platt scaling) mengunci rentang teoretis `dili_score`
ke `[~0.4337, ~0.7747]`; rentang EMPIRIS terukur atas 1.231 senyawa nyata (F1) bahkan lebih sempit lagi:
**[0.5078, 0.7329]**. Karena ambang hijau lama (0.30) berada JAUH di bawah rentang ini, hijau adalah
kode mati di `master`. Ketua Tim sudah memutuskan kalibrasi TIDAK diubah -- perbaikan dilakukan dengan
menurunkan ambang warna (`FUSION_AI_T_LOW`/`FUSION_AI_T_HIGH`, F2) dari distribusi nyata dan menstrukturkan
ulang lapisan fusi jadi matriks 9-sel eksplisit (F3). **Status: diperbaiki secara STRUKTURAL** (unit
test membuktikan `AI_LOW x LOW_EXPOSURE -> hijau`), TAPI lihat SS3 di bawah -- belum terbukti tercapai
lewat skenario pasien nyata end-to-end.

## 2. Temuan SS3.2 (`MODERATE_EXPOSURE` tidak berpengaruh) -- diperbaiki

Rantai `if/elif...or...` lama diganti matriks 9-sel eksplisit (F3). `AI_LOW x MODERATE_EXPOSURE`
sekarang menghasilkan KUNING, berbeda dari `AI_LOW x LOW_EXPOSURE` (HIJAU) -- dibuktikan lewat test
`test_ai_low_x_moderate_differs_from_ai_low_x_low`. **Status: diperbaiki, terbukti lewat test.**

## 3. \U0001F6A8 TEMUAN BARU (F2/F5, di luar SS3.1-3.5 dokumen asli): `LOW_EXPOSURE` praktis tidak terjangkau

Ditemukan saat membangun uji senyawa acuan F2: `exposure_evaluator.py` punya cacat struktural SEJENIS
SS3.1, tapi di layer berbeda dan BELUM diperbaiki. `PBPKEngine` adalah ODE LINEAR -- dosis menskalakan
`cmax_hati` dan `auc_hati` dengan faktor yang SAMA, sehingga `cmax_auc_ratio` **matematis tidak
bergantung pada dosis sama sekali**, hanya pada kovariat pasien. Sweep 20.250 kombinasi pasien+dosis
realistis (usia 18-90, BMI 16-40, dosis 0.5-50 mg/kg) menghasilkan **0% LOW_EXPOSURE** -- kategori ini
mati untuk kovariat pasien manapun yang diuji (laporan F2/F5 internal task; ringkasan di dokumen ini).

**Konsekuensi langsung:** karena matriks fusi (F3) memetakan `(AI_LOW, LOW_EXPOSURE) -> HIJAU`, dan
`LOW_EXPOSURE` praktis tidak terjangkau, **HIJAU BELUM TERBUKTI TERCAPAI lewat skenario pasien nyata
end-to-end** -- meski band AI-nya sendiri sudah benar (dibuktikan lewat senyawa vNo skor terendah
katalog, `test_vno_safe_compound_reaches_ai_low_band`, F8). Ini BUKAN kegagalan matriks F3 -- ini
keterbatasan LAPISAN LAIN (`exposure_evaluator.py`) yang di luar wewenang branch `fusion` untuk diubah
tanpa keputusan Farmasi (gerbang K3 -- lihat SS5). **DoD proyek "Hijau terbukti bisa muncul" HANYA
terpenuhi SEBAGIAN**: terbukti secara struktural (unit test, injeksi band langsung), BELUM terbukti
lewat request HTTP nyata dengan kovariat pasien apa pun yang sudah diuji.

**Rekomendasi:** gerbang K3 (enam ambang exposure) perlu diprioritaskan Farmasi SEGERA, bukan ditunda --
tanpa revisi ambang tersebut, klaim "digital twin yang personal" untuk warna HIJAU tidak bisa
didemonstrasikan ke juri dengan kovariat pasien apa pun.

> ### ✅ ADENDUM PASCA-MERGE master <-> fusion (resolusi konflik, 2026-08-09)
>
> Temuan SS3 di ATAS diselesaikan oleh evaluator yang termerge dari master:
> `exposure_evaluator.py` di master memakai kalibrasi eksposur v2.3 berbasis kuantil
> `P33_EXPOSURE_INDEX`/`P66_EXPOSURE_INDEX` (bukan enam ambang rasio lama
> `30.0/10.0/0.40/0.35/0.30/0.20` yang membuat `LOW_EXPOSURE` tak terjangkau).
> Dengan evaluator ini, dosis rendah pada kovariat pasien realistis KINI mencapai
> `LOW_EXPOSURE`, sehingga **HIJAU end-to-end (AI_LOW x LOW_EXPOSURE) terbukti
> tercapai lewat request HTTP nyata** -- diverifikasi oleh
> `tests/e2e/test_d9_fusion_e2e.py::test_vno_safe_compound_reaches_ai_low_band`
> (Calcitonin salmon, dosis 50 mg, usia 25/P/60kg/165cm -> `LOW_EXPOSURE` -> HIJAU).
> DoD proyek "Hijau terbukti bisa muncul" kini terpenuhi PENUH, bukan hanya struktural.
> Konfigurasi ambang exposure & kalibrasi v2.3 tetap di luar wewenang lapisan fusion
> (gerbang K3, review Farmasi) -- nilai P33/P66 dipertahankan apa adanya dari master.

## 4. `dili_score` tidak dipengaruhi kovariat pasien

`dili_score` murni fungsi SMILES (struktur molekul) -- diverifikasi lewat F1 (1.231 forward pass,
tidak ada parameter pasien yang masuk model AI). Personalisasi HANYA lewat jalur PBPK/`exposure_category`.
> *Catatan pasca-merge master<->fusion:* paragraf berikut menggambarkan perilaku evaluator enam ambang
> rasio LAMA; dengan kalibrasi kuantil v2.3 yang termerge, `LOW_EXPOSURE` kini terjangkau pada dosis
> rendah (lihat ADENDUM di §3).
Kombinasi dengan temuan SS3 di atas: karena `exposure_category` untuk sebagian besar skenario realistis
adalah HIGH_EXPOSURE (F5: 52/60 kombinasi profil contoh), **jalur personalisasi pasien pun kehilangan
sebagian besar variasinya** -- pada rentang dosis wajar, kovariat pasien seringkali tidak lagi mengubah
`exposure_category` (karena sudah HIGH sejak dosis kecil). Ini batas nyata klaim "digital twin" HepaTwin
dan harus dinyatakan eksplisit ke juri, bukan dikaburkan.

## 5. Enam ambang exposure adalah asumsi desain tanpa sitasi

`30.0`/`10.0` mg/kg, `0.40`/`0.35`/`0.30`/`0.20` (rasio Cmax/AUC) TIDAK bersitasi -- Soejima et al. (2022)
dan Ghabril et al. (2025) hanya mendukung KEBERADAAN modifikator usia>=60/BMI>=30, bukan nilai ambangnya.
> *Catatan pasca-merge master<->fusion:* enam ambang rasio ini telah digantikan evaluator v2.3 berbasis
> kuantil `P33/P66_EXPOSURE_INDEX` (`reports/pbpk_exposure_calibration_v2_3.md`); ambang exposure
> tersebut tetap di luar wewenang lapisan fusion (gerbang K3, review Farmasi).

## 6. Ambang warna AI (T_low/T_high) diturunkan dari distribusi katalog, bukan validasi klinis

Metode (b) (pemetaan-balik raw 0.30/0.70 lewat kalibrator, default gerbang K2) dipilih karena paling
mudah dijelaskan sebagai kelanjutan desain PRD awal -- BUKAN karena tervalidasi klinis independen.
Dua kandidat lain (tersier, biaya klinis) dihitung & dibandingkan (`reports/F2_penurunan_ambang.md`),
keputusan final tetap milik Farmasi + Ketua Tim.

## 7. Kontradiksi skor <-> zona (24 & 86 senyawa) -- tidak diperbaiki, sesuai rekomendasi dokumen

24 senyawa `vNo-DILI-concern` punya zona spesifik; 86 senyawa `vMost-DILI-concern` zonanya tidak
diketahui. Kedua sumber (DILIrank vs LiverTox) mengukur hal berbeda -- TIDAK "diperbaiki" dengan
memaksa konsistensi (akan mengarang data). `evidence_note` (F4) memakai kalimat netral, tidak mengklaim
"terbukti tidak ada cedera" (gerbang K6: skema DB belum membedakan "belum divalidasi" vs "sudah
divalidasi, tidak ada bukti" -- di luar cakupan `fusion`, perubahan skema DB terpisah).

## 8. Pemetaan zona histologis -> segmen Couinaud adalah penyederhanaan pedagogis

Wajib dinyatakan di Medical Disclaimer & presentasi (sudah ada di `disclaimer_permanent`,
`simulation_orchestrator.py`) -- rasio-R & zona histologis bersifat mikroskopis, Couinaud makrovaskular.
Tidak diubah di branch ini (di luar cakupan D7/D9).

## 9. \U0001F6A8 TEMUAN BARU (F4): `affected_segments` salah untuk 100% senyawa sejak awal, sekarang diperbaiki

Kode lama `simulation_orchestrator.py` memisah `segment_list` dengan koma (`split(",")`), padahal data
NYATA di Supabase memakai titik-koma (`;`) secara universal (diverifikasi query 1.231 senyawa). Akibatnya
`affected_segments` SELALU berisi satu string gabungan salah (mis. `["V;VI;VII;VIII"]`) alih-alih daftar
segmen individual, sejak kode ini pertama ada di `master` -- tidak pernah tertangkap test (mock lama
memakai koma, bukan data asli). **Diperbaiki di F4.** Ini murni bug lama, tidak terkait D7/D9 secara
konseptual, tapi ditemukan & diperbaiki di jalur kode yang sama.

## 10. \U0001F6A8 TEMUAN BELUM TUNTAS (F6): tail latency `shap_ms` tidak konsisten antar-run

Tiga run benchmark independen (`scripts/benchmark_simulation.py`, 150 panggilan/run, senyawa & profil
identik) menghasilkan DUA run cepat konsisten (shap_ms max ~48-52ms) dan SATU run dengan satu panggilan
`get_shap_detail()` memakan **~9.5 detik** (total request ~10.2 detik, melebihi anggaran 5 detik PRD
UC-02). Akar sebab BELUM ditemukan -- dugaan (belum terverifikasi): kompilasi/alokasi tunda yang hanya
terpicu molekul berukuran nyata (warm-up internal `HybridAIEngine._warm_up()` hanya memakai metana,
1 atom). Di luar wewenang `fusion` untuk mendiagnosis lebih dalam (`hepatwin_ml.explain()`, Alur C sudah
"selesai" per dokumen task). **Rekomendasi:** monitor `logger.info("F6 timing ...")` (sudah
terpasang) di staging/produksi sebelum mengklaim p95 seluruh katalog 1.231 senyawa aman tanpa syarat.

## 11. Cold start proses (~5-7 detik) tetap ada, tapi BUKAN bagian anggaran per-request

Direkonsiliasi dengan temuan lama `ml/reports/C12_limitations.md` (~8-10 detik): terurai jadibiaya boot proses SEKALI per lifecycle (import torch/RDKit + load model + JIT numba, ~5-7 detik, sebelum traffic
apa pun bisa dilayani) + request pertama SETELAH proses siap (~1.9-2.3 detik, DI BAWAH anggaran). Biaya
boot tetap relevan operasional (waktu deploy/restart) tapi bukan bagian DoD D7 (diukur via
`scripts/benchmark_cold_start.py`).

## 12. `PBPK_Engine_Audit_Report_v2_3.md` (pembaruan 2026-08-09)

Saat penulisan laporan ini, `PBPK_Engine_Audit_Report.md` tidak ditemukan di git history -- diduga berada
di luar repo (Google Docs tim, dsb). **Pembaruan:** dokumen tersebut kini ADA dan ter-track di root repo
sebagai `PBPK_Engine_Audit_Report_v2_3.md` (nama diselaraskan dengan daftar deliverable PRD §11.1;
berisi audit v2.3). Adendum "koreksi cakupan" (SS3.1/SS3.2 sebagai koreksi cakupan, bukan pembatalan
hasil LULUS) telah **digabungkan ke dokumen tersebut** sebagai "§6. Adendum (2026-08-09)" per
instruksi task.

## 13. Status gerbang K1-K6

Seluruh keputusan gerbang memakai default dokumen dan ditandai `[KEPUTUSAN AI -- PENDING REVIEW]`,
kecuali K6 (tidak diterapkan, sesuai default). **K3 kini mendesak** (lihat §3 di atas) -- bukan sekadar
item basa-basi review; dengan kalibrasi v2.3 yang termerge, urgensi K3 berkurang namun review Farmasi
tetap wajib (nilai P33/P66 dipertahankan apa adanya dari master).
