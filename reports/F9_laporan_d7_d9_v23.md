# F9 v2.3 -- Laporan Ringkas Revisi D7 & D9 (Branch `fusion`, R1-R7)

**Cakupan:** R1-R7, penyelarasan branch `fusion` (D7/D9, sudah menyelesaikan F0-F9 siklus v2.1) terhadap
PRD v2.3 setelah Ketua Tim meng-upgrade Mesin A (PBPK).

---

## Ringkasan tiap task

| Task | Yang ditemukan | Yang diubah | Artefak |
|---|---|---|---|
| **R1** | \U0001F6A8 Merge Mesin A sebelumnya (`95e53c7`) meninggalkan `simulation_orchestrator.py` TIDAK BISA DI-IMPORT (di luar cakupan resmi R1) | Diperbaiki sbg prasyarat; verifikasi nol divergensi Mesin A (pbpk_engine/pbpk_calibration/allometric_service identik master); 6 laporan v2.1 diarsipkan | `reports/R1_sinkronisasi.md` |
| **R2** | Sweep 20.250 kombinasi identik v2.1: LOW_EXPOSURE 0% -> **43.41%** | Tidak ada perubahan kode (murni pengukuran) | `reports/R2_exposure_reachability_v23.md`, `R2_sweep_raw.csv` |
| **R3** | HIJAU terbukti tercapai lewat **pipeline penuh**; 10/12 senyawa contoh berubah warna antar-profil pasien | Tidak ada perubahan kode; test lama diperbarui utk assert HIJAU end-to-end | `reports/R3_uji_acuan_v23.md` |
| **R4** | Jalur A (metabolic_risk_flag): 44.4% kombinasi kehilangan HIJAU bila diaktifkan. Jalur B (strong evidence): 407 senyawa (33.1%) selalu merah pd tafsiran terlonggar | **TIDAK ADA** perubahan `fusion_service.py` (sesuai desain task) | `reports/R4_dampak_eskalasi.md` |
| **R5** | -- | `metabolic_risk_flag`/`evidence_strength` + catatan naratif ditambahkan sbg field informatif, TIDAK memengaruhi warna | `app/models/schemas.py`, `simulation_orchestrator.py` |
| **R6** | `mapping_confidence` diminta PRD tapi tidak ada di DB | Proksi dari `livertox_match_method` ditambahkan, ditandai eksplisit sbg turunan; TIDAK ada kolom baru di Supabase | `app/models/schemas.py`, `simulation_orchestrator.py` |
| **R7** | -- | `risk_label_id`/`risk_label_disclaimer` ditambahkan (PRD v2.3 label wajib); `risk_level` tidak diubah | `app/models/schemas.py`, `simulation_orchestrator.py` |
| **R8** | -- | Regenerasi laporan (ini + limitasi + jury challenge + audit exposure + adendum PBPK) | `reports/F5_audit_exposure_v23.md`, `F9_limitations_fusion_v23.md`, `F9_jury_challenge_v23.md`, `F9_addendum_pbpk_audit.md` |

## Angka sebelum (v2.1) vs sesudah (v2.3)

| Metrik | v2.1 | v2.3 |
|---|---|---|
| LOW_EXPOSURE tercapai (sweep 20.250 kombinasi identik) | 0 (0.00%) | 8.791 (43.41%) |
| `exposure_index`/`cmax_auc_ratio` berubah thd dosis | Tidak (konstan matematis) | Ya (naik monoton) |
| HIJAU tercapai lewat pipeline penuh (bukan unit test) | Tidak terbukti | **Terbukti** (R3) |
| Senyawa acuan aman (Calcitonin salmon, dosis wajar) | HIGH_EXPOSURE -> KUNING/MERAH | LOW_EXPOSURE -> **HIJAU** |
| Variasi warna antar-profil pasien (12 senyawa sampel) | Minim terlihat | 10/12 berubah |
| Field response baru | -- | `+8`: `metabolic_risk_flag`, `metabolic_risk_note`, `evidence_strength`, `evidence_strength_note`, `livertox_match_method`, `mapping_confidence`, `mapping_confidence_source`, `risk_label_id`, `risk_label_disclaimer`, `segment_mapping_type`, `segment_mapping_not_clinical_localization` (v2.3 upstream) |
| Jumlah test pytest | 178 (setelah perbaikan R1) | 188 |

## Status gerbang keputusan

Lihat `reports/F9_limitations_fusion_v23.md` §12 untuk tabel lengkap K1-K6 (siklus v2.1) dan G1-G5
(siklus v2.3). Ringkas: seluruh gerbang memakai default dokumen, ditandai
`[KEPUTUSAN AI -- PENDING REVIEW]` di kode & laporan. **G4** (T_LOW/T_HIGH final) dan **G1** (ambiguitas
PRD soal `metabolic_risk_flag`) adalah dua yang paling mendesak utk ratifikasi Ketua Tim/Farmasi.

## Definition of Done (SS6 `PROJECT_FUSION_V23.md`)

| Kriteria | Status |
|---|---|
| `exposure_evaluator.py` identik `master` | \U00002705 (R1) |
| LOW_EXPOSURE terbukti terjangkau dgn angka | \U00002705 43.41% (R2) |
| HIJAU terbukti end-to-end lewat pipeline penuh | \U00002705 (R3) |
| Parasetamol MERAH, senyawa aman HIJAU | \U00002705 (R3) |
| Laporan F2/F5/F9 diregenerasi, versi lama diarsipkan | \U00002705 (R1, R8) |
| Dampak eskalasi diukur sebelum implementasi | \U00002705 (R4) |
| `livertox_match_method` diteruskan; `mapping_confidence` status jelas | \U00002705 (R6) |
| Label "Prioritas...in-silico" tersedia | \U00002705 (R7) |
| Ketiga warna terpakai pada katalog | \U00002705 (R3: 7.8%/74.0%/18.2% pd satu profil; R2 membuktikan variasi lebih luas lintas profil) |
| Fusi tetap 100% rule-based | \U00002705 (tidak diubah, diverifikasi test AST) |
| `pytest` hijau, tidak ada regresi | \U00002705 188 passed |

**Seluruh 11 kriteria DoD v2.3 terpenuhi** -- perbaikan signifikan dibanding siklus v2.1 (2 kriteria hanya
sebagian). Detail keterbatasan yang tetap ada (bukan kegagalan DoD, tapi batas jujur sistem) ada di
`reports/F9_limitations_fusion_v23.md`.
