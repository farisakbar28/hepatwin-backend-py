# EXECUTION_PLAN_FUSION.md — Rencana Eksekusi Agent (D7 & D9)

**Repo:** `hepatwin-backend-py`
**Branch:** `fusion`, dibuat dari `master`
**Dokumen induk:** `PROJECT_FUSION.md` — **WAJIB dibaca lebih dulu**
**Cakupan:** D7 (Endpoint Paralel-Asinkron) & D9 (Lapisan Fusi Rule-Based)
**Versi:** 1.0

---

## Aturan Main untuk Agent

1. **Baca `PROJECT_FUSION.md` sepenuhnya dulu.** Temuan §3.1 (hijau tidak pernah muncul) mengubah cara seluruh task ini dikerjakan.
2. **Kerjakan berurutan:** F0 → F1 → F2 → F3 → F4 → F5 → F6 → F7 → F8 → F9.
3. **Satu task = satu commit**, format `F<n>: <ringkasan>`.
4. **Jangan mengarang angka.** Distribusi & latensi dari eksekusi nyata.
5. **Kegagalan adalah keluaran yang sah.** Latensi > 5 detik → laporkan, jangan diakali.
6. **Berhenti di gerbang 🔴 K1–K5** (`PROJECT_FUSION.md` §6).
7. **Jangan melebarkan cakupan** (`PROJECT_FUSION.md` §5) — khususnya: **jangan sentuh kalibrasi**.
8. **`master` baca-saja.**
9. **Windows path:** forward slash atau `r"..."`.

---

## Peta Task

| Kode | Task | Map ke | Gerbang | Perkiraan |
|---|---|---|---|---|
| **F0** | Bootstrap branch `fusion` | — | — | 30 mnt |
| **F1** | Diagnostik distribusi skor katalog 1.231 senyawa | D9 | — | 2–3 jam |
| **F2** | Penurunan ambang `T_low`/`T_high` dari data | D9 | 🔴 K2 | 2 jam |
| **F3** | Refaktor `FusionService` jadi matriks 3×3 | D9 | 🔴 K1, K2 | 3 jam |
| **F4** | Intensitas & mode hotspot (gap PRD) | D9 | — | 2 jam |
| **F5** | Audit `exposure_evaluator` & penandaan asumsi | D9 | 🔴 K3, K5 | 2 jam |
| **F6** | Instrumentasi latensi & verifikasi paralelisme | **D7** | — | 3–4 jam |
| **F7** | Perluasan kontrak `SimulationResponse` | D7+D9 | 🔴 K4 | 2 jam |
| **F8** | Test suite fusi & latensi | D7+D9 | — | 3–4 jam |
| **F9** | Dokumentasi & laporan | D7+D9 | — | 2 jam |

**Jalur tidak terblokir:** F0 → F1 bisa langsung jalan. F2–F5 punya default sehingga tetap bisa dieksekusi sambil menunggu ratifikasi.

---

## F0 — Bootstrap Branch `fusion`

**Langkah:**
1. `git checkout master && git pull`
2. `git checkout -b fusion`
3. Salin `PROJECT_FUSION.md` & `EXECUTION_PLAN_FUSION.md` ke root repo.
4. Buat direktori `reports/` di root (terpisah dari `ml/reports/` yang milik Alur C) untuk laporan D7/D9.
5. Verifikasi baseline: `pytest` seluruh repo hijau **sebelum** perubahan apa pun. Catat hasilnya — ini titik acuan untuk mendeteksi regresi nanti.
6. Commit: `F0: bootstrap branch fusion untuk D7 & D9`

**Acceptance criteria:**
- [ ] Branch `fusion` bercabang dari commit terbaru `master`
- [ ] `pytest` baseline hijau dan jumlah test tercatat di `reports/F0_baseline.md`
- [ ] Tidak ada perubahan kode `app/` pada commit ini

---

## F1 — Diagnostik Distribusi Skor Katalog

**Tujuan:** dapatkan distribusi `dili_score` nyata atas seluruh 1.231 senyawa — ini fondasi seluruh keputusan ambang di F2.

> Tanpa data ini, ambang apa pun cuma tebakan. Task ini **wajib** selesai sebelum F2.

> ⚠️ **Data bergerak:** kurasi `injury_pattern`/LiverTox oleh Farmasi berjalan paralel dan aktif berubah (`PROJECT_FUSION.md` §4.4 catatan tambahan). Ini tidak memengaruhi `dili_score` (yang murni dari SMILES via model AI, sudah statis sejak C9), tapi **memengaruhi** validitas F4 (intensitas/zona) bila laporan dianggap "final" tanpa tanggal. Task ini fokus skor (aman dari isu itu); F4 yang perlu berhati-hati.

**File baru:** `scripts/diagnose_score_distribution.py`

**Langkah:**
1. Muat seluruh senyawa `is_simulatable = TRUE` dari Supabase (pakai ulang `CompoundRepository`). **Gunakan `SUPABASE_ANON_KEY`, bukan service role key.**
2. **Catat timestamp snapshot** (`snapshot_at`) di awal skrip — sertakan di setiap file keluaran. Ini murni untuk jejak audit, bukan karena skor `dili_score` sendiri berubah-ubah (skor statis, ditentukan SMILES).
3. Untuk tiap senyawa, jalankan `HybridAIEngine.predict_dili_risk(smiles)` → kumpulkan `dili_score` terkalibrasi.
   - Ini 1.231 forward pass. **Boleh di-batch** untuk kecepatan. Catat waktu totalnya.
   - SHAP **tidak perlu** dijalankan di sini — hanya skor.
4. Laporkan statistik: min, p1, p5, p10, p25, median, p33, p67, p75, p90, p95, p99, max.
5. Laporkan distribusi terpisah per `dili_concern` (vMost / vLess / vNo / Ambiguous) — ini menunjukkan apakah model benar-benar memisahkan kelas pada skala terkalibrasi.
6. **Verifikasi temuan §3.1:** konfirmasi batas bawah aktual (ekspektasi ≈ 0.4337) dan berapa senyawa yang jatuh di bawah 0.30 (ekspektasi: **nol**).
7. Hitung distribusi warna dengan **ambang lama** (0.30/0.70): berapa persen hijau/kuning/merah.
8. Simpan skor per senyawa ke `reports/F1_scores_catalogue.csv` (dengan kolom `snapshot_at`) — dipakai ulang di F2 & F8 supaya tidak perlu inferensi ulang.

**Keluaran:** `reports/F1_diagnostik_distribusi.md` + `reports/F1_scores_catalogue.csv`

**Acceptance criteria:**
- [ ] Seluruh 1.231 senyawa punya skor — bila ada yang gagal, daftarkan, jangan diam-diam dibuang
- [ ] `snapshot_at` tercatat di file keluaran
- [ ] Batas bawah aktual terverifikasi dan dilaporkan
- [ ] Jumlah senyawa berskor < 0.30 dilaporkan (ekspektasi 0 — bila bukan 0, temuan §3.1 perlu direvisi, laporkan)
- [ ] Distribusi warna dengan ambang lama terdokumentasi
- [ ] 🚩 Bila ternyata ada senyawa < 0.30, **hentikan dan laporkan** — asumsi dasar dokumen berubah

---

## F2 — Penurunan Ambang `T_low` & `T_high` 🔴 K2

**Tujuan:** ambang warna diturunkan dari data, bukan asumsi.

**Langkah:**
1. Memakai `F1_scores_catalogue.csv`, hitung **ketiga** kandidat ambang (`PROJECT_FUSION.md` §4.2):

   | Metode | Perhitungan |
   |---|---|
   | (a) Tersier | `T_low` = persentil-33, `T_high` = persentil-67 |
   | (b) Pemetaan-balik | Skor terkalibrasi yang setara raw 0.30 & 0.70 → ≈ 0.5458 & 0.6866 |
   | (c) Biaya klinis | `T_low` dipilih agar *false negative rate* pada senyawa `vMost`+`vLess` rendah |

2. Untuk **tiap** kandidat, laporkan:
   - Distribusi warna atas 1.231 senyawa (% hijau / kuning / merah)
   - Distribusi warna terpisah per `dili_concern` — idealnya `vNo` didominasi hijau, `vMost` didominasi merah
   - Sensitivity & specificity pada `T_low` bila diperlakukan sebagai ambang biner

3. **Uji senyawa acuan** untuk tiap kandidat:

   | Senyawa | Harapan |
   |---|---|
   | Parasetamol / Acetaminophen | MERAH (PRD UC-02) |
   | Beberapa senyawa `vNo-DILI-concern` | Setidaknya sebagian HIJAU |

4. 🔴 **Gerbang K2.** Default bila belum ada keputusan: **metode (b)**, karena mempertahankan maksud desain PRD awal dan paling mudah dijelaskan ke juri sebagai kelanjutan, bukan perubahan arbitrer. Tandai `[KEPUTUSAN AI — PENDING REVIEW FARMASI + KETUA TIM]`.
5. Simpan ambang terpilih ke **config** (`app/core/config.py`), **bukan** hardcoded di `fusion_service.py`.

**Keluaran:** `reports/F2_penurunan_ambang.md`

**Acceptance criteria:**
- [ ] Ketiga kandidat terhitung dengan distribusi lengkap
- [ ] Uji senyawa acuan terdokumentasi untuk ketiganya
- [ ] Ambang terpilih ada di config, bisa diubah tanpa menyentuh logika
- [ ] 🚩 Bila **tidak ada** kandidat yang bisa membuat parasetamol MERAH **dan** sebagian `vNo` HIJAU sekaligus — laporkan sebagai temuan, jangan paksakan salah satu

---

## F3 — Refaktor `FusionService` jadi Matriks 3×3 🔴 K1, K2

**Tujuan:** hilangkan cabang mati secara struktural, setia pada tabel PRD Bab 8.3.

**File:** `app/services/fusion_service.py`

**Langkah:**
1. Definisikan enum band AI: `AI_LOW` / `AI_MID` / `AI_HIGH`, memakai `T_low` & `T_high` dari config (F2).
2. Implementasikan matriks eksplisit (`PROJECT_FUSION.md` §4.1) sebagai **struktur data**, bukan rantai `if/elif`:

   ```
   MATRIX = {
     (AI_LOW,  EXP_LOW):      (low,    green,  none),
     (AI_LOW,  EXP_MODERATE): (medium, yellow, slow),
     (AI_LOW,  EXP_HIGH):     (high,   red,    fast),
     (AI_MID,  EXP_LOW):      (medium, yellow, slow),
     (AI_MID,  EXP_MODERATE): (medium, yellow, slow),
     (AI_MID,  EXP_HIGH):     (high,   red,    fast),
     (AI_HIGH, EXP_LOW):      (high,   red,    fast),
     (AI_HIGH, EXP_MODERATE): (high,   red,    fast),
     (AI_HIGH, EXP_HIGH):     (high,   red,    fast),
   }
   ```

   Keunggulan bentuk ini: seluruh 9 sel terlihat eksplisit, mudah diaudit juri, dan **tidak mungkin ada cabang tersembunyi yang tak tercapai**.

3. Tambahkan `fusion_reason` di keluaran — string singkat menjelaskan sel mana yang terpakai, mis. `"AI_MID x EXP_LOW"`. Ini membuat keputusan fusi dapat ditelusuri, bukan kotak hitam.
4. **Jangan ubah** nilai `risk_level` / `visual_color` / `blinking_speed` yang sudah dipakai frontend (`low`/`medium`/`high`, `green`/`yellow`/`red`, `none`/`slow`/`fast`) — kompatibilitas frontend harus terjaga.
5. Pertahankan sifat **rule-based murni** — tidak ada ML, tidak ada pembobotan yang dipelajari. Ini syarat eksplisit DoD D9.

**Acceptance criteria:**
- [ ] Seluruh 9 sel matriks tercakup test — **tidak ada sel yang tak tercapai**
- [ ] `AI_LOW × EXP_LOW` menghasilkan HIJAU (memperbaiki §3.1)
- [ ] `AI_LOW × EXP_MODERATE` menghasilkan KUNING, berbeda dari `AI_LOW × EXP_LOW` (memperbaiki §3.2 — membuktikan `MODERATE` kini bermakna)
- [ ] Ambang dibaca dari config
- [ ] Nilai enum keluaran tidak berubah dari `master`
- [ ] Tidak ada impor pustaka ML di `fusion_service.py`

---

## F4 — Intensitas & Mode Hotspot (Gap PRD §3.3)

**Tujuan:** teruskan `hotspot_base_intensity` & `hotspot_display_mode` yang sudah ada di database tapi tidak pernah dipakai.

**File:** `app/services/simulation_orchestrator.py`, `app/models/schemas.py`, `app/models/domain.py`

**Langkah:**
1. Pastikan model domain memuat `hotspot_base_intensity` dan `hotspot_display_mode`. Bila belum, tambahkan pemetaan kolomnya.
2. Teruskan keduanya ke `SimulationResponse` (field baru — lihat F7).
3. **Jaga pemisahan tanggung jawab** (`PROJECT_FUSION.md` §4.3):
   - warna & kedip ← **fusi** (seberapa berisiko)
   - segmen & intensitas ← **lookup DB** (di mana & seberapa kuat buktinya)

   🔴 **Jangan** mencampur `hotspot_base_intensity` ke dalam perhitungan warna. `dim` berarti "bukti lokasi lemah", **bukan** "risiko rendah". Mencampurnya akan membuat senyawa berisiko tinggi tanpa monograf LiverTox tampak aman — kebalikan dari prinsip antihalusinasi PRD.
4. 🔴 **K6 memengaruhi kalimat ini.** Database saat ini **tidak** membedakan "belum divalidasi Farmasi" vs "sudah divalidasi, memang tidak ada bukti" (`PROJECT_FUSION.md` §4.4). Karena itu `evidence_note` **wajib** memakai kalimat netral yang tidak mengklaim salah satu kondisi secara pasti:
   `"evidence_note": "Pola cedera spesifik untuk senyawa ini belum tersedia di data kurasi; hotspot ditampilkan difus redup sebagai default aman."`
   Hindari kalimat yang menyiratkan kepastian negatif seperti *"tidak ditemukan bukti"* atau *"terbukti tidak ada cedera spesifik"* — itu klaim lebih kuat dari yang bisa dipastikan sistem saat ini. Isi hanya bila `injury_pattern` = "Tidak Terklasifikasi" atau `segment_list` kosong.
5. Verifikasi fallback tetap berfungsi: senyawa tanpa `segment_list` → 8 segmen, `diffuse`, `dim`.

**Acceptance criteria:**
- [ ] `hotspot_base_intensity` & `hotspot_display_mode` muncul di respons
- [ ] Keempat kombinasi `injury_pattern` menghasilkan intensitas/mode yang benar (test tabel §4.3)
- [ ] `evidence_note` terisi hanya untuk kasus fallback, dengan kalimat netral (bukan klaim "terbukti tidak ada")
- [ ] Intensitas terbukti **tidak** memengaruhi warna (test eksplisit)

---

## F5 — Audit `exposure_evaluator` & Penandaan Asumsi 🔴 K3, K5

**Tujuan:** luruskan klaim yang tidak akurat (§3.4) dan tandai asumsi tanpa sitasi (§3.5). **Logikanya tidak diubah** kecuali Farmasi memutuskan lain.

**File:** `app/services/exposure_evaluator.py`

**Langkah:**
1. 🔴 **K5** — ganti `"threshold_line_used": False` menjadi nama yang akurat, mis. `"absolute_concentration_threshold_used": False`, dengan komentar yang jujur:
   > Sistem tidak memakai ambang konsentrasi toksik spesifik per senyawa (mis. mg/L), sesuai PRD Bab 8.3. Ambang **relatif seragam** (mg/kg dan rasio Cmax/AUC) tetap dipakai dan didefinisikan di bawah.

   Pertahankan field lama sebagai alias sementara bila frontend sudah memakainya — jangan pecahkan kontrak tanpa koordinasi.

2. 🔴 **K3** — beri komentar `[ASUMSI DESAIN — PENDING REVIEW FARMASI]` pada keenam angka (`30.0`, `10.0`, `0.40`, `0.35`, `0.30`, `0.20`), dengan penjelasan apa yang **memang** bersitasi:
   - Soejima et al. (2022) → mendukung *keberadaan* modifikator usia ≥ 60
   - Ghabril et al. (2025) → mendukung *keberadaan* modifikator BMI ≥ 30
   - **Nilai ambangnya sendiri: belum bersitasi**

3. Pindahkan keenam angka ke **config**, jangan hardcoded — supaya Farmasi bisa merevisi tanpa menyentuh logika.
4. Tambahkan analisis sensitivitas ringkas: dari 1.231 senyawa pada beberapa profil pasien contoh, berapa yang jatuh ke LOW/MODERATE/HIGH? Ini menunjukkan apakah ketiga kategori benar-benar terpakai atau ada yang praktis mati.

**Acceptance criteria:**
- [ ] Klaim `threshold_line_used` diperbaiki, kompatibilitas dijaga
- [ ] Keenam ambang ada di config + ditandai asumsi
- [ ] Analisis sensitivitas dilaporkan di `reports/F5_audit_exposure.md`
- [ ] 🚩 Bila ada kategori paparan yang praktis tidak pernah tercapai, laporkan sebagai temuan
- [ ] Logika tidak diubah tanpa keputusan Farmasi

---

## F6 — Instrumentasi Latensi & Verifikasi Paralelisme (**D7**)

**Tujuan:** membuktikan DoD D7 (**< 5 detik**) dengan angka, dan memastikan paralelismenya nyata.

> Saat ini **tidak ada instrumentasi apa pun** — DoD D7 belum bisa dibuktikan maupun dibantah.

**File:** `app/services/simulation_orchestrator.py`, `scripts/benchmark_simulation.py`

**Langkah:**

1. **Instrumentasi per-tahap.** Catat durasi: lookup DB, inferensi AI, SHAP, PBPK solve, evaluasi paparan, fusi, total. Log sisi server; **jangan** bocorkan ke response body kecuali diminta (K4).

2. **Verifikasi paralelisme nyata.** `asyncio.gather` + `run_in_executor` belum menjamin paralel — bila GIL tidak dilepas, eksekusinya bisa efektif berurutan.
   - Ukur: `t_total` vs `max(t_ai, t_shap, t_pbpk)` vs `t_ai + t_shap + t_pbpk`
   - Bila `t_total ≈ jumlah` → **tidak benar-benar paralel**, laporkan sebagai temuan
   - Bila `t_total ≈ maksimum` → paralelisme bekerja

3. **Periksa komputasi ganda.** `predict_dili_risk(smiles)` dan `get_shap_detail(smiles)` dipanggil sebagai dua task terpisah — keduanya melakukan standardisasi SMILES + featurisasi + forward pass. Ukur berapa besar duplikasinya. Bila signifikan, usulkan (jangan langsung terapkan) jalur gabungan yang berbagi hasil featurisasi.

4. **Cek thread-safety.** Model PyTorch dibagi antara dua thread executor (AI & SHAP) secara bersamaan. Verifikasi `model.eval()` + `torch.no_grad()` aktif dan tidak ada state yang dimutasi saat forward pass. Bila ragu, jalankan uji konkurensi: 20 permintaan bersamaan, pastikan hasilnya identik dengan permintaan tunggal.

5. **Benchmark.** Minimal **50 senyawa berbeda** × beberapa profil kovariat. Laporkan p50, p90, **p95**, p99, max. DoD memakai p95.

6. **Uji cold start vs warm.** Pemanggilan pertama (model load, JIT numba, cache kosong) hampir pasti lebih lambat. Laporkan keduanya terpisah — jangan sembunyikan cold start di balik rata-rata.

**Keluaran:** `reports/F6_latensi_d7.md`

**Acceptance criteria:**
- [ ] Instrumentasi per-tahap terpasang & terlog
- [ ] p95 end-to-end dilaporkan dengan angka nyata
- [ ] Status paralelisme dinyatakan tegas: **PARALEL** / **EFEKTIF BERURUTAN**, dengan bukti perbandingan waktu
- [ ] Cold start & warm dilaporkan terpisah
- [ ] Uji konkurensi 20 permintaan lulus (hasil identik)
- [ ] 🚩 Bila p95 > 5 detik → **laporkan apa adanya**. Jangan mematikan SHAP atau memangkas fitur diam-diam demi lolos angka; usulkan opsi optimasi ke Ketua Tim sebagai keputusan terpisah

---

## F7 — Perluasan Kontrak `SimulationResponse` 🔴 K4

**Tujuan:** teruskan informasi baru dari F3–F6 ke frontend tanpa memecah kontrak yang sudah ada.

**File:** `app/models/schemas.py`

**Usulan field baru** (semua **tambahan**, tidak ada yang dihapus/diubah — *backward compatible*):

| Field | Tipe | Isi | Asal |
|---|---|---|---|
| `hotspot_intensity` | `str` | `high` / `low` / `dim` | F4 |
| `hotspot_display_mode` | `str` | `focal` / `diffuse` | F4 |
| `evidence_note` | `str \| null` | Catatan bila pola cedera tidak tersedia | F4 |
| `fusion_reason` | `str` | Sel matriks terpakai, mis. `"AI_MID x EXP_LOW"` | F3 |
| `exposure_category` | `str` | `LOW_EXPOSURE` / `MODERATE_EXPOSURE` / `HIGH_EXPOSURE` | F3 |
| `thresholds_used` | `object` | `{t_low, t_high}` — transparansi ambang | F2 |
| `timing_ms` | `object \| null` | Durasi per tahap; hanya bila `settings.DEBUG` | F6 |

🔴 **K4** — wajib dikoordinasikan dengan Vedo (kontrak data) & Ketua Tim sebelum final.

**Acceptance criteria:**
- [ ] Seluruh field lama tetap ada dengan nama & tipe sama
- [ ] Test kontrak: respons lama tetap valid (tidak ada regresi frontend)
- [ ] `timing_ms` hanya muncul saat `DEBUG` aktif
- [ ] `openapi.json` diperbarui

---

## F8 — Test Suite Fusi & Latensi

**File:** `tests/unit/test_fusion_matrix.py`, `tests/e2e/test_d7_latency.py`, `tests/e2e/test_d9_fusion_e2e.py`

**Test wajib:**

| # | Kasus | Ekspektasi |
|---|---|---|
| 1 | Sembilan sel matriks | Semua tercakup, tidak ada yang tak tercapai |
| 2 | `AI_LOW × EXP_LOW` | HIJAU — **memperbaiki §3.1** |
| 3 | `AI_LOW × EXP_MODERATE` vs `AI_LOW × EXP_LOW` | Hasil **berbeda** — membuktikan `MODERATE` bermakna (§3.2) |
| 4 | Parasetamol | MERAH (PRD UC-02) |
| 5 | Senyawa `vNo` dosis wajar | HIJAU tercapai |
| 6 | Senyawa `is_simulatable = FALSE` | Ditolak, tidak masuk fusi (DoD D9) |
| 7 | `injury_pattern` = Hepatoseluler | Segmen V,VI,VII,VIII + `focal` + `high` |
| 8 | `injury_pattern` = Tidak Terklasifikasi | 8 segmen + `diffuse` + `dim` + `evidence_note` terisi |
| 9 | Intensitas tidak memengaruhi warna | Dua senyawa skor sama, intensitas beda → warna sama |
| 10 | Reproduktibilitas | Dua panggilan identik → respons identik |
| 11 | Latensi p95 | < 5 detik (DoD D7) |
| 12 | Konkurensi 20 permintaan | Hasil identik dengan permintaan tunggal |
| 13 | Fusi bebas ML | Tidak ada impor `torch`/`sklearn` di `fusion_service.py` |
| 14 | Regresi | Seluruh test `master` tetap hijau |

**Acceptance criteria:**
- [ ] Seluruh 14 kasus punya test dan lulus
- [ ] Test cakupan matriks memakai parametrize, bukan 9 fungsi terpisah
- [ ] `pytest` seluruh repo hijau, jumlah test ≥ baseline F0

---

## F9 — Dokumentasi & Laporan

**Langkah:**
1. **`reports/F9_laporan_d7_d9.md`** — rangkum F1–F8: apa yang ditemukan, apa yang diubah, angka sebelum vs sesudah.
2. **`reports/F9_limitations_fusion.md`** — wajib memuat:
   - Temuan §3.1: hijau tidak pernah muncul pada `master`, penyebabnya (rentang kalibrasi `[0.4337, 0.7747]`), dan bahwa perbaikannya dilakukan di lapisan fusi karena kalibrasi dibekukan Ketua Tim
   - Temuan §3.2: `MODERATE_EXPOSURE` sebelumnya tidak berpengaruh
   - **`dili_score` tidak dipengaruhi kovariat pasien** — personalisasi hanya lewat jalur PBPK/paparan. Ini batas nyata klaim "digital twin" dan harus dinyatakan, bukan dikaburkan
   - Enam ambang paparan adalah asumsi desain tanpa sitasi
   - Ambang warna diturunkan dari distribusi katalog, bukan dari validasi klinis
   - Kontradiksi skor↔zona (24 & 86 senyawa, `PROJECT_FUSION.md` §4.4)
   - Pemetaan zona histologis → segmen Couinaud adalah penyederhanaan pedagogis (wajib per PRD)
   - Status gerbang K1–K5
3. **Perbarui `PBPK_Engine_Audit_Report.md`** atau buat adendum: audit lama menyatakan LULUS tanpa cacat; temuan §3.1/§3.2 perlu dicatat sebagai koreksi cakupan — audit tersebut memverifikasi keselarasan struktur dengan PRD, bukan keterjangkauan cabang logika saat runtime. **Jangan hapus audit lama** — tambahkan adendum. Riwayat yang jujur lebih bernilai di Jury Challenge.
4. Siapkan ringkasan Jury Challenge: jawaban jujur untuk *"kenapa ambangnya diubah dari PRD?"*, *"apakah mengubah usia/berat benar-benar mengubah hasil?"*, *"bagaimana memastikan fusinya bukan ML?"*

**Acceptance criteria:**
- [ ] Seluruh angka dapat ditelusuri ke artefak `reports/`
- [ ] Adendum audit ditambahkan, audit lama tidak dihapus
- [ ] `F9_limitations_fusion.md` memuat seluruh butir di atas, termasuk yang tidak menguntungkan
- [ ] Status K1–K5 tercatat (diratifikasi atau masih pending)

---

## Ringkasan Gerbang

| ID | Pertanyaan | Ke siapa | Default | Memblokir |
|---|---|---|---|---|
| **K1** | Matriks 3×3 menggantikan rantai `or`? | Ketua Tim | Ya | F3 |
| **K2** | Nilai `T_low` & `T_high` | Farmasi + Ketua Tim | Metode (b): ≈0.5458 / ≈0.6866 | F2, F3 |
| **K3** | Enam ambang paparan | Farmasi | Dipertahankan, ditandai asumsi | F5 |
| **K4** | Field baru `SimulationResponse` | Ketua Tim + Vedo | Usulan F7 | F7 |
| **K5** | Ganti nama `threshold_line_used` | Ketua Tim | Ya | F5 |

Seluruh gerbang punya default — **tidak ada task yang benar-benar terhenti**, tapi setiap keluaran yang bergantung pada default wajib ditandai `[KEPUTUSAN AI — PENDING REVIEW]`.

---

## Definition of Done — Branch `fusion`

- [ ] F0–F9 selesai, masing-masing satu commit
- [ ] **Hijau terbukti bisa muncul** untuk senyawa yang memang aman
- [ ] **`MODERATE_EXPOSURE` terbukti berpengaruh**
- [ ] Ketiga warna terpakai pada katalog 1.231 senyawa, distribusinya dilaporkan
- [ ] Parasetamol MERAH, ada senyawa aman HIJAU
- [ ] `hotspot_base_intensity` & `hotspot_display_mode` diteruskan ke respons
- [ ] Latensi p95 dilaporkan dengan angka; status paralelisme dinyatakan tegas
- [ ] Fusi tetap 100% rule-based
- [ ] Hanya `is_simulatable = TRUE` yang diproses
- [ ] Kontrak API *backward compatible*
- [ ] Seluruh `pytest` hijau, tidak ada regresi
- [ ] Dokumentasi & adendum audit lengkap
