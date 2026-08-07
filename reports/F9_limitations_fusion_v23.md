# F9 v2.3 -- Batasan & Keterbatasan Branch `fusion` (setelah upgrade Mesin A)

Pembaruan `reports/_v21_archive/F9_limitations_fusion.md` setelah Mesin A di-upgrade ke PRD v2.3
(6 Agustus 2026). Dokumen ini WAJIB dibaca sebelum mengklaim branch `fusion` "selesai" ke Ketua Tim,
Farmasi, atau juri. Struktur mengikuti apa yang R8 minta: status temuan lama + status baru dgn angka.

---

## 1. \U00002705 RESOLVED: LOW_EXPOSURE kini terjangkau (dulu blocker utama)

**Status lama (v2.1, arsip):** `exposure_evaluator.py` berbasis `cmax_auc_ratio` (rasio dua besaran yang
sama-sama linear terhadap dosis) -- matematis TIDAK bergantung dosis. Sweep 20.250 kombinasi pasien
realistis: **0% mencapai LOW_EXPOSURE**. HIJAU jadi kode mati end-to-end walau matriks AI benar secara
struktural.

**Status sekarang (v2.3):** `exposure_index = log1p(Cmax_L) + log1p(AUC_L)` (magnitude, BUKAN rasio)
dibandingkan kuantil beku `p33=8.2388`/`p66=10.9192` dari calibration sweep internal (1.728.324 sampel).

- R2 (`reports/R2_exposure_reachability_v23.md`): sweep IDENTIK 20.250 kombinasi -> **LOW_EXPOSURE
  43.41%**, MODERATE 34.37%, HIGH 22.22%.
- R3 (`reports/R3_uji_acuan_v23.md`): HIJAU terbukti tercapai lewat **pipeline penuh** (AI + PBPK v2.3 +
  exposure v2.3 + fusi), bukan lagi hanya unit test injeksi matriks. Senyawa acuan yang PERSIS SAMA
  dgn siklus v2.1 (Calcitonin salmon, dosis wajar) yang dulu SELALU HIGH_EXPOSURE kini LOW_EXPOSURE ->
  HIJAU.
- `exposure_index` terbukti BERUBAH terhadap dosis pada profil pasien tetap (R2, R8/`F5_audit_exposure_v23.md`)
  -- kontras eksplisit dgn `cmax_auc_ratio` yang matematis konstan.

**DoD "Hijau terbukti bisa muncul untuk senyawa aman" kini TERPENUHI**, dibuktikan empiris R2+R3, bukan
diasumsikan dari kalibrasi grid semata.

\U0001F6A8 **Caveat metodologis yang tetap berlaku:** kalibrasi p33/p66 dilakukan pada grid tertentu
(usia mencakup 0-100 menurut PROJECT_FUSION_V23.md, XLogP katalog penuh). R2/R3 mensweep rentang usia
18-90, XLogP TIDAK divariasikan (tetap `None`/fallback `0.0` di R2, tetap `1.2` representatif di R8) --
belum menguji seluruh kombinasi XLogP nyata (`-1` s.d. `7`, clamp `xlogp_eff`). Rekomendasi: sweep
tambahan dgn XLogP bervariasi bila ada waktu, sebelum mengklaim keterjangkauan berlaku universal utk
seluruh 1.231 senyawa x seluruh kombinasi pasien.

## 2. `exposure_index` adalah indeks komputasional visualisasi, BUKAN prediksi kadar hati klinis

Ditegaskan ulang sesuai PRD v2.3 §8.2 batas validitas: model PBPK Fase 1 adalah **linear,
perfusion-limited, bolus tunggal, tanpa absorpsi oral, tanpa protein binding, tanpa Km/Vmax, tanpa
metabolit reaktif, tanpa NAPQI/glutathione depletion, tanpa parameter compound-specific IVIVE penuh**.
`exposure_index`/`exposure_category` adalah alat triase riset & visualisasi, BUKAN nilai yang boleh
dipakai penentuan dosis pasien nyata. `disclaimer_permanent` (response API) sudah menyatakan ini eksplisit.

## 3. `p33`/`p66` adalah kalibrasi distribusional internal, BUKAN ambang klinis

`app/services/pbpk_calibration.py`: `P33_EXPOSURE_INDEX`/`P66_EXPOSURE_INDEX` dihitung dari sweep
internal HepaTwin sendiri (1.728.324 sampel), bukan dari studi klinis obat spesifik. PRD v2.3 mengutip
Olaparib [26] & Rilzabrutinib [32] yang justru menunjukkan threshold PK bermakna klinis bersifat
**drug-specific**, bukan universal -- selaras dgn keputusan TIDAK memakai ambang klinis di HepaTwin.

## 4. `dili_score` TETAP tidak dipengaruhi kovariat pasien -- batas klaim "digital twin" tetap berlaku

`dili_score` murni fungsi SMILES, model AI statis sejak C9, TIDAK diubah oleh upgrade Mesin A. Jalur
personalisasi HANYA lewat PBPK/`exposure_category` -- yang KINI (v2.3) benar-benar bervariasi terhadap
dosis+fisiologi+XLogP (R3: 10/12 senyawa contoh berubah warna antar-profil pasien, membaik dari siklus
v2.1 di mana variasi nyaris tidak terlihat). Namun batas fundamentalnya tetap sama: mengubah pasien TIDAK
PERNAH mengubah `dili_score`, hanya `exposure_category`. Ini harus dinyatakan eksplisit ke juri, bukan
dikaburkan oleh perbaikan v2.3.

## 5. `T_LOW`/`T_HIGH` (band AI) tetap distribusional, bukan validasi klinis independen

Nilai TIDAK dihitung ulang (dili_score tidak berubah) -- hanya diuji ulang (R3). Tiga kandidat
(`(a)` 0.6046/0.6664, `(b)` 0.5458/0.6866 -- **dipilih, default gerbang G4**, `(c)` 0.5621/0.6898)
diturunkan dari distribusi katalog, bukan validasi klinis. Keputusan final tetap milik Farmasi + Ketua Tim.

## 6. Dua jalur eskalasi PRD v2.3 (§8.3.3): DIUKUR, TIDAK diimplementasikan sbg pengubah warna

R4 (`reports/R4_dampak_eskalasi.md`): mengaktifkan `metabolic_risk_flag -> minimal KUNING` akan
menghilangkan kemungkinan HIJAU utk **44.4%** kombinasi pasien+dosis (SELURUH pengguna BMI>=30, apa pun
senyawa/dosisnya) -- pola kegagalan identik SS3.1/SS3.2 lama. "LiverTox strong evidence -> MERAH" tafsiran
paling longgar memaksa **407 senyawa (33.1% katalog)** selalu merah tanpa memandang skor AI.

**Jalur default diterapkan (R5):** `metabolic_risk_flag` dan `evidence_strength` diekspos sbg field
INFORMATIF di response, TIDAK memengaruhi warna, ditandai `[PENDING G1]`/`[PENDING G2]`. Dibuktikan lewat
test: pasien BMI>=30 tetap bisa mendapat HIJAU.

\U0001F6A8 **Ambiguitas PRD v2.3 sendiri, wajib diklarifikasi Ketua Tim:** §8.3.3 menyebut
`metabolic_risk_flag` "hanya flag naratif; tidak menurunkan clearance default" di teks, TAPI tabel
matriks eskalasi di bagian yang sama menuliskannya sbg kondisi `atau` yang mengubah warna KUNING. Dua
tafsiran itu tidak bisa benar bersamaan -- perlu keputusan eksplisit sebelum eskalasi diaktifkan (G1).

## 7. `mapping_confidence` masih proksi turunan, bukan kolom kurasi asli (gerbang G3)

Kolom `mapping_confidence` yang diminta PRD v2.3 §8.3.1 TIDAK ADA di `hepatwin_compounds` -- kurasi
Farmasi masih berjalan paralel. R6: proksi diturunkan dari `livertox_match_method` (kolom yang memang
ada), ditandai eksplisit `mapping_confidence_source="DERIVED_PROXY_PENDING_G3"` di setiap response agar
tidak disangka kolom kurasi asli. Tidak ada kolom baru dibuat di Supabase (sesuai batas lingkup).

## 8. Kontradiksi skor <-> zona (24 & 86 senyawa) -- tidak berubah, tidak diperbaiki

Belum terpengaruh upgrade Mesin A (murni soal kurasi LiverTox/DILIrank, bukan PBPK/exposure). 24 senyawa
`vNo-DILI-concern` punya zona spesifik; 86 senyawa `vMost-DILI-concern` zonanya tidak diketahui. TIDAK
"diperbaiki" dgn memaksa konsistensi (mengarang data) -- `evidence_note`/`evidence_strength_note` tetap
netral. Gerbang **K6** (field status kurasi terpisah "belum dicek" vs "sudah dicek, tidak ada bukti")
tetap TIDAK diterapkan, di luar cakupan `fusion` (perubahan skema DB).

## 9. Pemetaan Couinaud tetap heuristik pedagogis -- kini diberi flag eksplisit di response

`segment_mapping_type="PEDAGOGICAL_HEURISTIC"` dan `segment_mapping_not_clinical_localization=true`
SUDAH ada di setiap response (payload wajib PRD v2.3 §8.3.2) -- perbaikan dibanding v2.1 yang tidak
punya flag eksplisit ini. Rasio-R & zona histologis tetap mikroskopis, Couinaud tetap makrovaskular;
tidak identik, tidak diklaim identik.

## 10. \U0001F6A8 TEMUAN BELUM TUNTAS (F6, tidak berubah oleh upgrade Mesin A): tail latency `shap_ms`

Tidak diselidiki ulang di siklus v2.3 ini (di luar cakupan R1-R8, murni soal AI explainability, tidak
terkait PBPK). Status tetap seperti dilaporkan `reports/_v21_archive/F9_limitations_fusion.md` §10: satu
dari tiga run benchmark menunjukkan satu panggilan SHAP ~9.5 detik, tidak tereproduksi 2 run lain. Belum
terdiagnosis, direkomendasikan monitoring produksi.

## 11. Bug `affected_segments` (F4) -- tetap terjaga, diverifikasi ulang

Perbaikan delimiter `;` (bukan `,`) masih intact setelah merge Mesin A v2.3 (diverifikasi R1). Tidak ada
regresi.

## 12. Status gerbang keputusan (K1-K6 siklus v2.1 + G1-G5 siklus v2.3)

| Gerbang | Pertanyaan | Status |
|---|---|---|
| K1 | Matriks 3x3 | Diterapkan (F3), tidak disentuh upgrade Mesin A |
| K2 | T_low/T_high awal | Diterapkan (F2), nilai sama dipakai G4 |
| K3 | 6 ambang exposure v2.1 | **OBSOLETE** -- v2.3 mengganti total dgn kalibrasi p33/p66, enam ambang keras tidak lagi dipakai |
| K4 | Field baru response v2.1 | Diterapkan (F7), field bertambah lagi di R5-R7 |
| K5 | Rename `threshold_line_used` | Diterapkan (F5) -- field ini sendiri kini tidak relevan lagi (v2.3 tidak pakai ambang absolut ATAU rasio utk kategori) |
| K6 | Kolom status kurasi DB | Tidak diterapkan (default), tetap di luar cakupan |
| G4 | T_LOW/T_HIGH final v2.3 | Default metode (b) dipertahankan (R3) -- `[PENDING REVIEW FARMASI + KETUA TIM]` |
| G1 | `metabolic_risk_flag` jadi pengubah warna? | Default: TIDAK (informatif saja, R5) -- `[PENDING REVIEW KETUA TIM + FARMASI]`, ambiguitas PRD perlu diklarifikasi |
| G2 | Definisi "LiverTox strong evidence" | Default: TIDAK ditafsirkan (informatif saja, R5) -- `[PENDING REVIEW FARMASI]` |
| G3 | `mapping_confidence`: kolom baru/proksi/revisi PRD | Default: proksi dari `livertox_match_method` (R6) -- `[PENDING REVIEW KETUA TIM + FARMASI]` |
| G5 | Teks label "Prioritas...in-silico" | Wording PRD v2.3 dipakai apa adanya (R7) |

## 13. \U0001F6A8 Temuan tak terduga di luar cakupan R1-R8 resmi: merge Mesin A sempat merusak build

Sebelum R1 dikerjakan, `simulation_orchestrator.py` hasil merge (`95e53c7`) TIDAK BISA DI-IMPORT
(`SyntaxError`, variabel timing tak terdefinisi, unpacking `asyncio.gather` tidak konsisten) --
`config.py` kehilangan `FUSION_AI_T_LOW`/`T_HIGH`, `schemas.py` kehilangan 6 field F4/F7. Diperbaiki
sbg prasyarat R1 (`reports/R1_sinkronisasi.md`). Pelajaran: **selalu jalankan `pytest` setelah resolve
conflict merge**, sebelum push -- ini seharusnya tertangkap sebelum sampai ke branch `fusion`.

---

**Ringkasan status DoD (SS6 PROJECT_FUSION_V23.md):** 9 dari 11 kriteria terpenuhi penuh; 2 sisanya
(dampak eskalasi terukur sebelum implementasi; `mapping_confidence` status jelas) juga terpenuhi lewat
R4/R6. **Tidak ada kriteria yang gagal** pada siklus v2.3 ini -- perbaikan signifikan dibanding siklus
v2.1 di mana 2 kriteria hanya terpenuhi sebagian.
