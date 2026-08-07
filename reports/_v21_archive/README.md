# Arsip Laporan v2.1

Laporan di direktori ini ditulis terhadap `exposure_evaluator` versi v2.1 (berbasis `cmax_auc_ratio`
dan enam ambang keras `30.0/10.0/0.40/0.35/0.30/0.20`). Mesin A telah di-upgrade ke v2.3
(`exposure_index` + kuantil kalibrasi beku `p33`/`p66`) pada 6 Agustus 2026, sehingga isi laporan ini
**tidak lagi menggambarkan sistem yang berjalan**.

Diarsipkan sebagai jejak audit temuan → perbaikan, bukan sebagai dokumentasi aktif. Versi terkini ada
di `reports/` (lihat `R2_exposure_reachability_v23.md`, `R3_uji_acuan_v23.md`,
`F9_limitations_fusion_v23.md`, `F9_laporan_d7_d9_v23.md`, `F9_jury_challenge_v23.md`,
`F5_audit_exposure_v23.md`).

**Isi arsip:**
- `F2_exposure_reachability_finding.md` — sweep 20.250 kombinasi v2.1: 0% mencapai `LOW_EXPOSURE`. Ini
  temuan yang memicu Ketua Tim meng-upgrade Mesin A ke v2.3.
- `F2_penurunan_ambang.md` — penurunan ambang T_low/T_high band AI (metode ini **masih valid** di v2.3,
  `dili_score` tidak berubah — hanya uji senyawa acuannya yang diulang di `R3_uji_acuan_v23.md`).
- `F5_audit_exposure.md` — audit enam ambang keras v2.1 (dosis mg/kg, rasio Cmax/AUC).
- `F9_limitations_fusion.md`, `F9_laporan_d7_d9.md`, `F9_jury_challenge.md` — laporan akhir F0-F9
  terhadap sistem v2.1, sebelum upgrade Mesin A.
