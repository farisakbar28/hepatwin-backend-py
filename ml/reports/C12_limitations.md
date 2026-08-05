# C12_limitations.md — Keterbatasan (Dicatat Jujur, Bukan Disembunyikan)

Aturan Main #2 (`EXECUTION_PLAN_FIX_MODEL.md`): kegagalan adalah keluaran
yang sah. Dokumen ini mendaftar SELURUH keterbatasan yang ditemukan selama
C1–C11, termasuk yang tidak menguntungkan proyek.

## 1. Ukuran dataset kecil untuk model deep learning

Korpus training = **870 senyawa** (529 positif / 341 negatif). Untuk
arsitektur graph attention + DNN hybrid (~880 ribu parameter), ini kecil —
risiko overfitting tidak sepenuhnya hilang meski sudah dimitigasi (dropout,
weight decay, early stopping, scaffold-disjoint split). Std antar-seed
relatif kecil (val_auc 0.6586±0.0029, C6) menunjukkan training stabil, tapi
tidak menghilangkan risiko generalisasi terbatas di luar distribusi
DILIrank/LiverTox.

## 2. Label DILIrank bukan pengukuran laboratorium langsung

`dili_concern` berasal dari teks label FDA (tingkat kekhawatiran) dan
kausalitas literatur (DILIrank 2.0), **bukan** hasil uji laboratorium
langsung per senyawa. Model belajar memprediksi *kategori kekhawatiran FDA*,
bukan *toksisitas terukur* — perbedaan yang harus dikomunikasikan ke
pengguna, bukan diabaikan.

## 3. `Ambiguous-DILI-concern` dibuang dari training, tapi tetap bisa dipilih pengguna

336 dari 1.231 senyawa `is_simulatable=TRUE` berlabel `Ambiguous-DILI-concern`
— dibuang dari korpus training (C5) karena tidak punya label biner yang sah.
**Model tidak pernah belajar dari kategori ini, tapi senyawanya tetap muncul
di autocomplete** (Keputusan Desain Final, database tertutup). Konsekuensi:
untuk 336 senyawa ini, prediksi model adalah **ekstrapolasi murni** di luar
distribusi training — tidak ada jaminan kualitas yang sama dengan 870 senyawa
yang benar-benar dipelajari. Ini harus dinyatakan eksplisit ke pengguna
(mis. badge/disclaimer terpisah), bukan diabaikan.

## 4. Zona kerusakan adalah lookup deterministik, bukan prediksi model

`histologic_zone`/`segment_list`/dst. adalah tabel lookup 1:1 dari
`injury_pattern` (LiverTox) — **bukan** keluaran model AI apa pun
(`PROJECT_FIX_MODEL.md` §4.1, diverifikasi: tidak ada satu baris pun yang
menyimpang dari pemetaan). 824 dari 1.231 senyawa `is_simulatable=TRUE`
**tidak punya monograf LiverTox** → jatuh ke fallback "Tidak Terklasifikasi"
(diffuse, redup) — bukan karena model tidak yakin, tapi karena data sumber
memang tidak ada.

## 5. Pemetaan pola cedera → segmen Couinaud adalah penyederhanaan pedagogis

Zona histologis (Zona 1/2/3) bersifat **mikroskopis**; segmentasi Couinaud
yang divisualisasikan bersifat **makroanatomis**. Pemetaan antara keduanya
adalah penyederhanaan untuk tujuan edukasi, bukan korespondensi anatomis
presisi — PRD sendiri mewajibkan disclaimer ini ditampilkan ke pengguna.

## 6. Bentuk garam direduksi ke fragmen terbesar

`standardize.py` (C2) memilih fragmen terbesar dari SMILES multi-fragmen
(566/1231 = 46% senyawa). Komponen lain pada garam kombinasi (mis.
klavulanat pada amoksisilin-klavulanat, bila ada di database) **tidak ikut
direpresentasikan** dalam graf/fingerprint — model hanya "melihat" komponen
aktif utama, bukan efek gabungan formulasi.

## 7. Kalibrator Platt degenerate pada threshold 0.5 (C7)

🔴 **Temuan tidak menguntungkan.** Kalibrator Platt (dipilih otomatis karena
VAL hanya 116 sampel, <200) menghasilkan probabilitas GATNN-DNN yang hampir
selalu ≥0.5 pada test set — confusion matrix menunjukkan **0 prediksi kelas
0** (specificity=0, MCC=0) meski AUC-ROC (ranking) tetap wajar (0.7252).
Diagnosis (lewat eksekusi, bukan asumsi): probabilitas mentah model jarang
turun di bawah ~0.21–0.23, sementara VAL 63.8% berlabel positif — kombinasi
ini membuat regresi logistik 1D belajar intercept yang nyaris tak pernah
terlampaui turun di bawah 0.5 pada rentang yang benar-benar muncul. **Bukan
bug kode** (fit hanya pada VAL, diterapkan ke TEST, sesuai desain) — ini
keterbatasan nyata kalibrator Platt pada set kalibrasi kecil & tidak
seimbang. **Implikasi produk:** `risk_level` (ambang 0.30/0.70 di
`simulation_orchestrator.py`) yang memakai `dili_score` terkalibrasi ini
akan condong sistematis ke kategori risiko lebih tinggi. Rinci:
`ml/reports/C7_evaluasi.md`.

## 8. Metode atribusi atom bukan Shapley sebenarnya

`method="masking_attribution"` (C8) — occlusion 1-fitur per atom, **bukan**
nilai Shapley (yang mensyaratkan rata-rata atas seluruh koalisi subset atom,
infeasible untuk molekul besar). Dilabeli jujur di kode & API, tidak disebut
"SHAP" meski secara konsep serupa. Tidak menangkap efek interaksi antar-atom.
Topologi edge tetap ada saat fitur node atom di-mask — delta yang terukur
adalah batas bawah kontribusi sebenarnya, bukan isolasi sempurna.

## 9. Nama & interpretasi klinis 9 pola SMARTS belum divalidasi Farmasi (Gerbang G4)

Diwarisi `upscale` apa adanya (nitro & fenol sudah diperbaiki secara
kimia-komputasi, tapi nama & interpretasi klinis seperti "Beta-lactam ring"
→ implikasi risiko belum ditinjau ahli farmasi). Jangan ditampilkan ke
pengguna akhir sebagai fakta terkurasi sebelum ACC tertulis Farmasi diterima.

## 10. Latensi request pertama pada proses baru (C10)

🔴 **Temuan tidak menguntungkan, belum tuntas diselesaikan.** Request
PERTAMA ke `POST /simulate` pada proses backend yang baru start memakan
**~8–10 detik** — melanggar anggaran PRD UC-02 (≤5 detik) — diverifikasi
lewat uvicorn sungguhan (bukan hanya `TestClient`), bukan asumsi. Request
kedua dst konsisten ~1–1.5 detik. Warm-up (main thread + concurrent executor
warm-up saat startup, `app/main.py`) terbukti mempercepat pemanggilan
langsung (`asyncio.run`, tanpa lewat HTTP) dari ~6 detik ke <10ms, **tapi
tidak cukup menghilangkan latensi request HTTP pertama** — akar masalah
pasti belum ditemukan (diduga interaksi ASGI server/anyio dengan thread
pool `asyncio.get_running_loop().run_in_executor(None, ...)`, bukan lagi
inisialisasi PyTorch/RDKit itu sendiri, yang sudah terbukti teratasi lewat
pengukuran langsung). **Dampak praktis:** hanya memengaruhi request
pengguna PERTAMA setelah setiap deploy/restart proses — pola "cold start"
yang umum di layanan ML, tapi tetap perlu diselidiki lebih lanjut atau
dimitigasi operasional (mis. *readiness probe*/warm-up request sintetis
sebelum lalu lintas nyata dirutekan) sebelum rilis produksi.

## 11. Bug pra-eksisting di luar cakupan Alur Kerja C (ditemukan, dicatat, sebagian diperbaiki dengan izin)

Rincian lengkap: `ml/reports/backlog.md`.

1. `simulation_orchestrator.py` men-split `segment_list` dengan koma padahal
   data Supabase memakai titik koma — **TIDAK diperbaiki** (Alur F, PIC Faris).
2. `CompoundDetail`/`compounds.py` mengakses 9 field PubChem descriptor yang
   tidak pernah ada di skema Supabase nyata — **DIPERBAIKI** (izin eksplisit
   Ketua Tim/Faris, diverifikasi tidak melanggar `HepaTwin_PRD.md`).
3. `compound_repository.py.get_compound_by_hepatwin_id()` membuat
   `SessionLocal()` sendiri, mengabaikan dependency injection `self.db` —
   **TIDAK diperbaiki** (file eksplisit terlarang disentuh,
   `PROJECT_FIX_MODEL.md` §6). Konsekuensi: 1 test
   (`test_b5_integration.py::test_operational_error_handling`) tetap merah
   di seluruh riwayat commit `fix-model` — bukan regresi dari Alur Kerja C,
   didokumentasikan bukan disembunyikan.
4. `app/models/domain.py` tidak pernah ter-commit di git manapun (master
   maupun `fix-model`) — **DIREKONSTRUKSI** (izin eksplisit pengguna) dari
   skema live Supabase (42 kolom, diverifikasi query langsung) supaya
   `app/` bisa di-import & di-test sama sekali.

## 12. Ringkasan "pytest seluruh repo hijau" — hampir, dengan satu pengecualian terdokumentasi

`pytest tests/ ml/tests/` → **202 passed, 1 failed**. Satu kegagalan
(`test_b5_integration.py::test_operational_error_handling`) adalah bug
pra-eksisting di file yang eksplisit terlarang disentuh (§11 poin 3) — bukan
regresi, bukan diabaikan diam-diam, dicatat di sini dan di `backlog.md`
sebagai penyimpangan sadar dari AC literal "pytest seluruh repo hijau".

## Ringkasan siap-presentasi Jury Challenge

Lihat halaman terpisah: `ml/reports/C12_ringkasan_jury.md`.
