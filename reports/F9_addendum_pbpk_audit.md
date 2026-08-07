# Adendum untuk `PBPK_Engine_Audit_Report.md`

> **Catatan penempatan:** `EXECUTION_PLAN_FUSION.md` F9 meminta adendum ini ditambahkan ke
> `PBPK_Engine_Audit_Report.md` yang sudah ada, TANPA menghapus isi audit lama. Pencarian menyeluruh
> (`git log --all -- "*PBPK_Engine_Audit*"` di seluruh branch) **tidak menemukan file ini di repository**.
> Kemungkinan dokumen tersebut ada di luar git (mis. Google Docs internal tim), sesuai konteks memori
> proyek. Adendum ini ditulis sebagai file mandiri di `reports/` -- **tim WAJIB menyalinnya ke dokumen
> audit asli begitu lokasinya ditemukan**, sesuai instruksi asli.

---

## Adendum: Koreksi Cakupan (bukan Pembatalan Hasil LULUS)

Audit PBPK sebelumnya menyatakan **LULUS tanpa cacat**. Untuk mesin PBPK itu sendiri (solver ODE 4-kompartemen,
penskalaan alometrik, verifikasi mass balance, optimasi Numba/LRU cache) penilaian tersebut **tepat dan
tidak dibantah** oleh temuan branch `fusion` -- diverifikasi ulang secara independen lewat 143 test
pre-existing yang tetap hijau, plus F6 (parallellisme AI‖PBPK terverifikasi nyata, PBPK konsisten
tercepat dari tiga tugas paralel, p50 ~0.5ms).

**Yang TIDAK tercakup audit lama** (bukan salah audit -- audit itu memeriksa keselarasan struktur kode
terhadap PRD, bukan keterjangkauan cabang logika saat runtime dengan data nyata):

1. **Lapisan fusi (`fusion_service.py`)**, yang mengonsumsi keluaran PBPK (lewat `exposure_evaluator.py`),
   punya cabang mati struktural (§3.1/§3.2 `PROJECT_FUSION.md`) -- diperbaiki di branch `fusion` (F3).

2. **`exposure_evaluator.py`** (F2/F5, branch `fusion`): karena `PBPKEngine` menyelesaikan ODE LINEAR,
   `cmax_hati` dan `auc_hati` diskalakan oleh faktor dosis yang SAMA -- sehingga `cmax_auc_ratio` yang
   dipakai `exposure_evaluator.py` **matematis tidak bergantung pada dosis sama sekali**, hanya pada
   kovariat pasien (via parameter alometrik). Ini BUKAN cacat pada solver ODE PBPK itu sendiri (linearitas
   adalah pilihan desain model yang sah dan terverifikasi mass-balance benar) -- ini adalah cacat pada
   BAGAIMANA lapisan di atasnya (`exposure_evaluator.py`) menafsirkan keluaran linear tersebut lewat
   enam ambang yang, setelah diukur (F5), ternyata membuat `LOW_EXPOSURE` praktis tidak terjangkau untuk
   kovariat pasien realistis manapun (0/20.250 kombinasi tersweep, `reports/F2_exposure_reachability_finding.md`).

**Rekomendasi update audit:** tambahkan catatan bahwa audit LULUS berlaku untuk KEBENARAN numerik
solver PBPK (ODE, alometrik, mass balance) -- bukan jaminan bahwa LAPISAN KONSUMEN (`exposure_evaluator.py`,
`fusion_service.py`) menafsirkan rentang keluarannya secara bermakna di seluruh tiga kategori
LOW/MODERATE/HIGH yang dirancang PRD. Riwayat yang jujur (audit tetap LULUS untuk cakupannya sendiri +
catatan keterbatasan cakupan) lebih bernilai untuk Jury Challenge daripada mengklaim audit itu mencakup
lebih dari yang sebenarnya diperiksa.

**Referensi (v2.1, diarsipkan):** `PROJECT_FUSION.md` §2 (tabel status komponen), §3.1-3.2,
`reports/_v21_archive/F2_exposure_reachability_finding.md`, `reports/_v21_archive/F5_audit_exposure.md`,
`reports/_v21_archive/F9_limitations_fusion.md` §3.

---

## Adendum v2.3 (6 Agustus 2026) -- Mesin A di-upgrade, temuan §2 di atas DITUTUP

Adendum di atas ditulis 5 Agustus 2026 terhadap Mesin A **v2.1**. Pada **6 Agustus 2026**, Ketua Tim
meng-upgrade Mesin A ke **v2.3**: `exposure_evaluator.py` diganti total dari `cmax_auc_ratio` (rasio
dose-independent) menjadi `exposure_index = log1p(Cmax_L) + log1p(AUC_L)` (magnitude, dose-dependent)
dibandingkan kuantil beku `p33`/`p66` dari calibration sweep internal (1.728.324 sampel,
`app/services/pbpk_calibration.py`).

**Temuan §2 poin 2 di atas (LOW_EXPOSURE tidak terjangkau) kini DITUTUP, dibuktikan empiris:**
- R2 (`reports/R2_exposure_reachability_v23.md`): sweep 20.250 kombinasi IDENTIK dgn v2.1 -- LOW_EXPOSURE
  0.00% (v2.1) -> **43.41%** (v2.3).
- R3 (`reports/R3_uji_acuan_v23.md`): HIJAU terbukti tercapai lewat **pipeline penuh** (bukan hanya unit
  test), termasuk utk senyawa acuan yang sama (Calcitonin salmon) yang dulu selalu HIGH_EXPOSURE.
- `exposure_index` terbukti berubah terhadap dosis (R2, R8/`F5_audit_exposure_v23.md`) -- kontras
  langsung dgn `cmax_auc_ratio` yang matematis konstan.

**Yang TIDAK berubah dari poin 1 di atas** (matriks fusi 3x3, F3): tetap benar dan tidak disentuh upgrade
Mesin A -- `git diff master fusion -- app/services/pbpk_engine.py app/services/pbpk_calibration.py
app/services/allometric_service.py` kosong (R1), membuktikan mesin PBPK v2.3 itu sendiri tidak
mengandung perubahan yang tidak sengaja dari branch `fusion`.

**Status akhir utk audit asli:** kesimpulan 5 Agustus ("LULUS utk cakupannya sendiri, TIDAK mencakup
lapisan konsumen") **tetap berlaku** -- yang berubah adalah lapisan konsumen (`exposure_evaluator.py`)
kini SUDAH menafsirkan keluaran PBPK secara bermakna di ketiga kategori, hasil kerja Ketua Tim di luar
cakupan `fusion`, diverifikasi ulang oleh branch ini (R1-R3).

**Referensi (v2.3):** `PROJECT_FUSION_V23.md` §1 (ringkasan perubahan Mesin A), §2 (verifikasi kode),
`reports/R1_sinkronisasi.md`, `reports/R2_exposure_reachability_v23.md`, `reports/R3_uji_acuan_v23.md`,
`reports/F5_audit_exposure_v23.md`.
