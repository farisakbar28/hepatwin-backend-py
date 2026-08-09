# F9 -- Laporan Ringkas D7 & D9 (Branch `fusion`)

**Cakupan:** F0-F8, branch `fusion` (dari `master` commit `e0e7e77`)
**DoD sumber:** `PROJECT_FUSION.md` SS7, `EXECUTION_PLAN_FUSION.md`

---

## Ringkasan tiap task

| Task | Yang ditemukan | Yang diubah | Artefak |
|---|---|---|---|
| **F0** | Baseline `master` TIDAK hijau (5 error `NameError: mock_get_db` di `test_api.py`, bug fixture pre-existing) | Diperbaiki (fixture disatukan); baseline resmi 143 passed | `reports/F0_baseline.md` |
| **F1** | Rentang `dili_score` empiris katalog 1.231 senyawa: **[0.5078, 0.7329]** (lebih sempit dari batas teoretis [0.4337, 0.7747] SS3.1 -- konsisten, bukan kontradiksi). 0/1231 di bawah 0.30 -- **cabang hijau lama terkonfirmasi kode mati** | Tidak ada perubahan kode (murni diagnostik) | `reports/F1_diagnostik_distribusi.md`, `F1_scores_catalogue.csv` |
| **F2** | 3 kandidat ambang dihitung. **TEMUAN BARU:** `exposure_evaluator.py` punya cacat struktural sejenis SS3.1 -- `cmax_auc_ratio` tidak bergantung dosis (ODE linear), LOW_EXPOSURE praktis tak terjangkau (0/20.250 kombinasi realistis) | Ambang dipilih (metode b, default K2) disimpan ke config | `reports/F2_penurunan_ambang.md`, `F2_exposure_reachability_finding.md` |
| **F3** | -- | `FusionService` direfaktor jadi matriks 9-sel eksplisit; hijau & MODERATE_EXPOSURE kini bermakna secara struktural (SS3.1/SS3.2 diperbaiki di lapisan fusi) | `app/services/fusion_service.py` |
| **F4** | **TEMUAN BARU:** `affected_segments` SALAH utk 100% dari 1.231 senyawa sejak awal -- kode lama `split(",")` tidak pernah menemukan pemisah pada data nyata (pemisah asli `;`) | Diperbaiki; `hotspot_intensity`/`hotspot_display_mode`/`evidence_note` diteruskan ke response (SS3.3) | `reports/F4_hotspot_intensitas.md` |
| **F5** | Enam ambang exposure tanpa sitasi (SS3.5); klaim `threshold_line_used` tidak akurat (SS3.4) | Nama field diperbaiki (alias dijaga), ambang dipindah ke config + ditandai asumsi, TIDAK diubah nilainya | `reports/F5_audit_exposure.md` |
| **F6** | Paralelisme AI‖SHAP‖PBPK **nyata** (wall-time ≈ max, bukan jumlah). Cold start lama "~8-10s" terurai jadi boot proses (~5-7s, di luar anggaran per-request) + request pertama (~1.9-2.3s, DI BAWAH anggaran). **TEMUAN BELUM TUNTAS:** satu dari tiga run menunjukkan `shap_ms` ~9.5 detik, tak tereproduksi 2 run lain | Instrumentasi per-tahap ditambahkan (`timing_sink`, log server-side) | `reports/F6_latensi_d7.md`, `F6_cold_start_terisolasi.md` |
| **F7** | `openapi.json` lama korup (UTF-16 hasil PowerShell salah encode) | Field baru ditambahkan (backward-compatible): `fusion_reason`, `exposure_category`, `thresholds_used`, `timing_ms` (gated `DEBUG`); `openapi.json` diregenerasi valid | `app/models/schemas.py` |
| **F8** | -- | 23 test baru (9 sel matriks, referensi PRD, fallback hotspot, latensi, konkurensi) | `tests/unit/test_fusion_matrix.py`, `tests/e2e/test_d9_fusion_e2e.py`, `tests/e2e/test_d7_latency.py` |

## Angka sebelum vs sesudah

| Metrik | Sebelum (`master`) | Sesudah (`fusion`) |
|---|---|---|
| Senyawa HIJAU tercapai (ambang 0.30, dili_score) | 0 / 1231 (0%) | Struktural: LULUS (unit test `test_ai_low_x_low_exposure_is_green`). End-to-end pasien nyata: **belum**, lihat `F9_limitations_fusion.md` |
| `MODERATE_EXPOSURE` berpengaruh pada output | Tidak pernah (kode mati) | Ya -- `AI_LOW x MODERATE_EXPOSURE` != `AI_LOW x LOW_EXPOSURE` (test eksplisit) |
| `affected_segments` benar | 0% (100% senyawa dapat 1 string salah) | 100% (parsing `;` benar) |
| `hotspot_base_intensity`/`hotspot_display_mode` di response | Tidak ada | Ada, dgn `evidence_note` fallback |
| Jumlah test pytest | 143 (baseline F0, setelah fix bug pre-existing) | 166 (+23) |
| p95 latensi end-to-end (warm, HTTP) | Tidak pernah diukur | 0.22-0.59s (3 run berbeda), jauh di bawah 5s |
| `openapi.json` valid | Tidak (korup) | Ya |

## Status gerbang keputusan

| Gerbang | Keputusan diambil | Status |
|---|---|---|
| K1 (matriks 3x3) | Ya, diterapkan (default dokumen) | `[KEPUTUSAN AI -- PENDING REVIEW KETUA TIM]` |
| K2 (T_low/T_high) | Metode (b) pemetaan-balik, 0.5458/0.6866 | `[KEPUTUSAN AI -- PENDING REVIEW FARMASI + KETUA TIM]` |
| K3 (6 ambang exposure) | Dipertahankan, ditandai asumsi, dipindah ke config | `[KEPUTUSAN AI -- PENDING REVIEW FARMASI]`, **mendesak** setelah temuan F2 (LOW_EXPOSURE tak terjangkau) |
| K4 (field baru response) | Diterapkan sesuai usulan F7 | `[KEPUTUSAN AI -- PENDING REVIEW KETUA TIM + VEDO]` |
| K5 (rename `threshold_line_used`) | Ya, `absolute_concentration_threshold_used`, alias dijaga | `[KEPUTUSAN AI -- PENDING REVIEW KETUA TIM]` -- default dokumen "Ya" |
| K6 (field status kurasi DB) | Tidak diterapkan (di luar cakupan, sesuai default) | Tidak memblokir, `evidence_note` pakai kalimat netral |

Lihat `reports/F9_limitations_fusion.md` untuk batasan yang belum tuntas dan `reports/F9_jury_challenge.md` untuk ringkasan tanya-jawab.
