# PROJECT_FUSION.md — Konteks & Spesifikasi Branch `fusion`

**Proyek:** HepaTwin — GEMASTIK XIX 2026, Tim Kicau Mania
**Branch:** `fusion`, dibuat dari `master`
**Cakupan:** **D7** (Endpoint Simulasi Paralel-Asinkron) & **D9** (Lapisan Fusi Rule-Based)
**PIC:** Faris (utama), kontrak data & integrasi dengan Vedo (C8/C10)
**Versi:** 1.0
**Status:** Draft — beberapa butir menunggu ratifikasi Ketua Tim / Farmasi (§6)

> **Untuk agent (Claude Code):** baca dokumen ini SELURUHNYA sebelum menyentuh kode. Dokumen ini menjelaskan *apa* dan *mengapa*; `EXECUTION_PLAN_FUSION.md` menjelaskan *bagaimana* dan *urutannya*. Ada satu temuan kritis (§3.1) yang membuat sebagian besar logika fusi saat ini **tidak pernah tereksekusi** — melewatkannya berarti membangun di atas fondasi yang rusak.

---

## 1. Definisi Task dari Dokumen Kerja Internal

| Kode | Tugas | DoD |
|---|---|---|
| **D7** | Endpoint Simulasi Paralel-Asinkron (AI + PBPK) — menjalankan AI Predictor dan PBPK Solver secara paralel sesuai arsitektur proposal serta **mengukur waktu respons keseluruhan** | Endpoint menghasilkan keluaran AI dan PBPK dalam satu respons dengan waktu total **< 5 detik** (NFR-02) |
| **D9** | Lapisan Fusi Rule-Based — menggabungkan probabilitas AI dan metrik paparan PBPK melalui aturan berbasis logika (**bukan** machine learning), menentukan warna hotspot dan kecepatan kedip, serta mengambil `segment_list` dari Supabase | Payload JSON akhir (segmen, warna, kecepatan kedip) dihasilkan sesuai aturan proposal, **hanya** untuk senyawa `is_simulatable = TRUE` |

**Dependensi:** D7 ← C10 & D6. D9 ← C8, D7, & B7. Seluruh dependensi **sudah selesai** di `master`.

---

## 2. Kondisi Awal: Apa yang Sudah Ada di `master`

Berbeda dari branch sebelumnya, D7 dan D9 **sudah terimplementasi sebagian** di `master`. Branch `fusion` adalah pekerjaan **audit, perbaikan, dan penyempurnaan** — bukan membangun dari nol.

| Komponen | File | Status |
|---|---|---|
| Orkestrasi paralel-asinkron | `app/services/simulation_orchestrator.py` | ✅ Ada — `asyncio.gather` + `run_in_executor` |
| Mesin AI (GATNN-DNN + SHAP) | `app/services/ai_engine.py` | ✅ Selesai (C1–C12) |
| Mesin PBPK 4-kompartemen | `app/services/pbpk_engine.py` | ✅ Selesai, lulus audit |
| Penskalaan alometrik | `app/services/allometric_service.py` | ✅ Selesai |
| Evaluator paparan | `app/services/exposure_evaluator.py` | ⚠️ Ada, tapi ada isu (§3.4, §3.5) |
| **Lapisan fusi** | `app/services/fusion_service.py` | 🔴 **Ada, tapi 2 dari 3 cabangnya tidak pernah tereksekusi (§3.1, §3.2)** |
| Lookup segmen Couinaud | di dalam orchestrator | ⚠️ Ada, tapi belum lengkap vs PRD (§3.3) |
| **Instrumentasi latensi** | — | 🔴 **Belum ada sama sekali** — DoD D7 tidak bisa dibuktikan |

**Catatan tentang `PBPK_Engine_Audit_Report.md`:** audit itu menyatakan LULUS tanpa cacat, dan untuk mesin PBPK-nya sendiri (ODE, alometrik, mass balance, optimasi numba/LRU) penilaian itu **tepat dan tidak dibantah dokumen ini**. Namun audit tersebut **tidak menguji lapisan fusi terhadap rentang keluaran aktual `dili_score`** — ia memeriksa keselarasan struktur kode dengan PRD, bukan apakah cabang-cabang logikanya benar-benar dapat tercapai saat dijalankan. Temuan §3.1 di bawah tidak terlihat oleh audit gaya itu.

---

## 3. 🔴 LIMA TEMUAN — WAJIB DIPAHAMI SEBELUM MULAI

Seluruh temuan berikut diverifikasi lewat eksekusi kode terhadap artefak nyata di `master`, bukan pembacaan kode semata.

### 3.1 🔴 KRITIS: Warna hijau tidak pernah bisa muncul

Kalibrator produksi (`app/models/calibrator_gatnn_dnn.pkl`) adalah Platt scaling yang di-*fit* pada probabilitas (bukan logit), dengan koefisien `a = 1.5016`, `b = −0.2667`. Konsekuensinya rentang keluaran `dili_score` terkunci:

| Input mentah model | `dili_score` yang keluar |
|---|---|
| `raw = 0.00` (model sangat yakin AMAN) | **0.4337** ← batas bawah absolut |
| `raw = 1.00` (model sangat yakin BAHAYA) | **0.7747** ← batas atas absolut |

Sementara `fusion_service.py` mensyaratkan `dili_score < 0.30` untuk hijau.

**0.4337 > 0.30 → cabang hijau adalah kode mati.** Tidak ada satu pun dari 1.231 senyawa yang bisa menghasilkan hijau, apa pun kovariat pasiennya.

**Ini melanggar PRD secara langsung.** PRD UC-02 mendefinisikan skenario yang wajib bisa terjadi:

> *"3D Hati (Panel Kanan): Seluruh 8 Segmen Couinaud menunjukkan visualisasi **BERWARNA HIJAU STABIL TANPA KEDIPAN (STABLE GREEN)** dengan intensitas difus redup."*

Skenario ini **mustahil dicapai** dengan konfigurasi saat ini.

> **Keputusan Ketua Tim:** skema kalibrasi **tidak diubah** — dipakai apa adanya, langsung lanjut ke D7/D9. Karena itu perbaikan **wajib dilakukan di lapisan fusi**, yaitu dengan menurunkan ulang ambang warna dari distribusi skor yang benar-benar dihasilkan. Ini sah: Ketua Tim sendiri sudah menyatakan ambang 0.30/0.70 "cuma sekadar asumsi desain, jadi bisa disesuaikan".

### 3.2 🔴 `MODERATE_EXPOSURE` tidak berpengaruh apa pun

Logika saat ini:

```python
if dili_score > 0.70 or exposure == HIGH:      # -> merah
elif dili_score >= 0.30 or exposure == MODERATE:  # -> kuning
else:                                           # -> hijau
```

Karena `dili_score >= 0.30` **selalu benar** (batas bawah 0.4337), operator `or` pada baris kedua selalu terpenuhi oleh kondisi pertama — kondisi `exposure == MODERATE` tidak pernah ikut menentukan hasil.

Hasil simulasi seluruh kombinasi (dieksekusi, bukan dugaan):

| `dili_score` | EXP_LOW | EXP_MODERATE | EXP_HIGH |
|---|---|---|---|
| 0.4337 (min) | KUNING | KUNING | MERAH |
| 0.5000 | KUNING | KUNING | MERAH |
| 0.7000 | KUNING | KUNING | MERAH |
| 0.7747 (max) | MERAH | MERAH | MERAH |

Kolom `EXP_MODERATE` **identik** dengan `EXP_LOW` di setiap baris. Seluruh logika fusi saat ini menyusut menjadi:

```
MERAH  jika (dili_score > 0.70) ATAU (exposure == HIGH)
KUNING selain itu
HIJAU  tidak pernah
```

**Implikasi untuk klaim produk:** HepaTwin dipresentasikan sebagai *digital twin* yang mempersonalisasi hasil berdasarkan usia, berat, tinggi, dan dosis. Namun `dili_score` **hanya bergantung pada struktur molekul (SMILES)** — sama sekali tidak dipengaruhi kovariat pasien. Satu-satunya jalur pengaruh kovariat adalah lewat `exposure_category`, dan karena `MODERATE` mati, kovariat hanya berpengaruh ketika ia mendorong paparan sampai `HIGH`. Untuk sebagian besar kombinasi, **mengubah profil pasien tidak mengubah apa pun di layar.** Ini risiko nyata bila juri mencoba mengubah usia/berat saat demo.

### 3.3 PRD menyebut `hotspot_base_intensity`, tapi kode tidak memakainya

Kueri lookup di PRD Bab 8.3 mengambil tiga kolom:

```sql
SELECT segment_list, injury_pattern, hotspot_base_intensity FROM hepatwin_compounds ...
```

Orchestrator saat ini hanya memakai `segment_list` dan `injury_pattern`. **`hotspot_base_intensity` tidak pernah dibaca**, dan tidak ada field intensitas apa pun di `SimulationResponse`.

Akibatnya dua ketentuan PRD tidak terimplementasi:
- Pola Campuran seharusnya tampil dengan **"intensitas visual menengah"**
- Senyawa tanpa monograf LiverTox seharusnya tampil **"hotspot difus redup"** (PRD UC-02: *"intensitas difus redup"*)

Saat ini keduanya tampil dengan intensitas yang sama seperti senyawa berpola spesifik — perbedaan tingkat keyakinan bukti hilang di layar. Padahal justru ini yang menjaga prinsip antihalusinasi medis PRD: senyawa tanpa bukti monograf **tidak boleh terlihat sama meyakinkannya** dengan senyawa yang punya bukti.

### 3.4 Klaim "tanpa ambang absolut" tidak sepenuhnya akurat

`exposure_evaluator.py` mengembalikan `"threshold_line_used": False` dengan komentar *"Penegasan eksplisit bahwa ambang absolut TIDAK digunakan"*. Namun kode yang sama memuat:

```python
if dose_per_kg >= 30.0 or cmax_auc_ratio > high_threshold:   # 0.35 / 0.40
elif dose_per_kg >= 10.0 or cmax_auc_ratio > moderate_threshold:  # 0.20 / 0.30
```

Angka `30.0`, `10.0`, `0.40`, `0.35`, `0.30`, `0.20` adalah **ambang absolut** — hanya saja pada besaran yang berbeda (mg/kg dan rasio Cmax/AUC), bukan pada konsentrasi toksik per senyawa.

**Maksud PRD sebenarnya benar dan tetap terpenuhi:** yang ditolak PRD adalah *garis ambang konsentrasi toksik spesifik per obat* (mis. "hepatotoksik di atas 150 mg/L"), karena nilai seperti itu hanya tervalidasi untuk sedikit obat. Sistem memang tidak memakai itu.

Yang perlu diperbaiki adalah **penamaan dan klaimnya**, bukan logikanya. Field `threshold_line_used: False` sebaiknya diganti menjadi sesuatu yang akurat, mis. `absolute_concentration_threshold_used: False`, disertai catatan bahwa ambang relatif seragam tetap dipakai. Bila dibiarkan, klaim ini mudah dipatahkan juri yang membaca kode.

### 3.5 Enam angka ambang paparan tidak punya rujukan

PRD mengutip Soejima et al. (2022) dan Ghabril et al. (2025) — tapi keduanya mendukung **keberadaan faktor modifikator** (usia ≥ 60, BMI ≥ 30), **bukan** nilai ambang `30.0 mg/kg`, `10.0 mg/kg`, `0.40`, `0.35`, `0.30`, `0.20`.

Keenam angka itu adalah asumsi desain tanpa sitasi. Itu **tidak apa-apa** untuk alat edukasi — asalkan **dinyatakan sebagai asumsi**, bukan disajikan seolah berbasis literatur. Saat ini tidak ada penandaan apa pun di kode maupun laporan.

---

## 4. Rancangan Lapisan Fusi yang Diusulkan

### 4.1 Ganti rantai `or` menjadi matriks 3×3 eksplisit

PRD Bab 8.3 menyajikan logika fusi sebagai **tabel matriks**, bukan rantai kondisi. Implementasi sebagai matriks eksplisit lebih setia pada PRD, lebih mudah diaudit juri, dan menghilangkan cabang mati secara struktural.

|  | `EXP_LOW` | `EXP_MODERATE` | `EXP_HIGH` |
|---|---|---|---|
| **`AI_LOW`** (skor < T_low) | 🟢 HIJAU / stabil | 🟡 KUNING / lambat | 🔴 MERAH / cepat |
| **`AI_MID`** (T_low ≤ skor ≤ T_high) | 🟡 KUNING / lambat | 🟡 KUNING / lambat | 🔴 MERAH / cepat |
| **`AI_HIGH`** (skor > T_high) | 🔴 MERAH / cepat | 🔴 MERAH / cepat | 🔴 MERAH / cepat |

Matriks ini setia pada PRD (baris merah PRD memakai "ATAU", baris kuning memakai "ATAU Ada Faktor Risiko Usia/BMI"), tapi **membuat `MODERATE` kembali bermakna**: sel `AI_LOW × EXP_MODERATE` menghasilkan KUNING, bukan HIJAU. Inilah jalur yang membuat kovariat pasien benar-benar terlihat pengaruhnya — memperbaiki §3.2.

### 4.2 Ambang `T_low` dan `T_high` diturunkan dari distribusi nyata

Karena kalibrasi dibekukan, ambang harus disesuaikan dengan rentang `[0.4337, 0.7747]` yang benar-benar dihasilkan.

**Sumber data untuk penurunan ambang:** distribusi `dili_score` atas **seluruh 1.231 senyawa `is_simulatable = TRUE`** — bukan test set.

> Ini penting secara metodologis: menurunkan ambang dari 1.231 senyawa katalog adalah keputusan **presentasi/UX**, bukan seleksi model. Test set (n=174) sudah dibuka sekali di C7; memakainya lagi untuk menyetel ambang akan menjadi kebocoran. Menghindarinya sepenuhnya dengan memakai katalog penuh.

Tiga kandidat metode (dibandingkan, bukan dipilih buta — lihat F2):

| Metode | Cara | Sifat |
|---|---|---|
| **(a) Persentil/tersier** | T_low = persentil-33, T_high = persentil-67 dari 1.231 skor | Menjamin ketiga warna terpakai proporsional; ambang murni relatif |
| **(b) Pemetaan-balik ambang lama** | Cari skor terkalibrasi yang setara dengan raw 0.30 dan 0.70 → T_low ≈ 0.5458, T_high ≈ 0.6866 | Mempertahankan *maksud* desain awal; paling mudah dijelaskan sebagai kelanjutan PRD |
| **(c) Berbasis biaya klinis** | T_low ditetapkan agar *false negative rate* rendah (lebih aman salah menandai bahaya daripada salah menandai aman) | Paling sesuai untuk alat keselamatan obat |

**Rekomendasi AI/ML:** kombinasi (b) sebagai titik awal, divalidasi dengan (c) — lalu diverifikasi dengan uji senyawa acuan. Keputusan final ada di Farmasi + Ketua Tim (gerbang **K2**, §6).

**Uji senyawa acuan wajib** (kalau gagal, ambangnya belum benar):

| Senyawa | Label DILIrank | Warna yang diharapkan |
|---|---|---|
| Parasetamol / Acetaminophen | `vMost-DILI-concern` | 🔴 MERAH (sesuai PRD UC-02) |
| Senyawa `vNo-DILI-concern` dosis wajar | `vNo-DILI-concern` | 🟢 HIJAU harus **bisa** tercapai |

### 4.3 Tambahkan intensitas hotspot (memperbaiki §3.3)

Ambil `hotspot_base_intensity` dari database dan teruskan ke frontend sebagai field baru. Pemetaannya sudah deterministik di database:

| `injury_pattern` | `hotspot_base_intensity` | `hotspot_display_mode` | Segmen |
|---|---|---|---|
| Hepatoseluler | `high` | `focal` | V, VI, VII, VIII |
| Kolestatik | `high` | `focal` | II, III, IV |
| Campuran | `low` | `diffuse` | I–VIII |
| Tidak Terklasifikasi | `dim` | `diffuse` | I–VIII (fallback) |

**Prinsip pemisahan yang wajib dijaga:**
- **Warna & kecepatan kedip** ← hasil fusi AI + PBPK (*seberapa berisiko*)
- **Segmen & intensitas** ← lookup database (*di mana, dan seberapa kuat buktinya*)

Keduanya **tidak boleh dicampur**. Intensitas `dim` menyampaikan "bukti lokasinya lemah", bukan "risikonya rendah" — dan itu justru pesan antihalusinasi yang diminta PRD.

### 4.4 Kontradiksi skor↔zona: tampilkan, jangan sembunyikan

Dari analisis database (temuan lama, kini relevan langsung ke D9):

| Pola | n | Yang terjadi di layar |
|---|---|---|
| `vNo-DILI-concern` **tapi** punya zona spesifik | 24 | Skor rendah, tapi segmen tertentu ter-highlight `focal` + `high` |
| `vMost-DILI-concern` **tapi** zona tidak diketahui | 86 | Skor tinggi/merah, tapi hotspot `diffuse` + `dim` |

Ini **bukan bug** — kedua sumber mengukur hal berbeda (`dili_concern` = tingkat kekhawatiran FDA; `injury_pattern` = pola cedera yang dilaporkan LiverTox *bila* cedera terjadi).

> **Klarifikasi penting (dari diskusi tim, 6 Agustus 2026):** dua baris di tabel atas punya penyebab **berbeda**, jangan disamakan:
>
> - **86 kasus (`vMost` tanpa zona)** kemungkinan besar **bukan** kontradiksi permanen — kurasi LiverTox oleh anggota Farmasi masih berjalan paralel dengan pekerjaan branch ini (validasi manual, ratusan senyawa, makan waktu). Sebagian dari 86 ini kemungkinan berstatus **"belum sempat divalidasi"**, bukan **"sudah divalidasi, memang tidak ada bukti"**. Angka ini diperkirakan mengecil seiring kurasi berlanjut.
> - **76 kasus (label bertentangan pada 409 senyawa overlap)** **tidak** termasuk kategori ini — kedua sumber untuk 76 senyawa ini **sudah** lengkap datanya, hanya berbeda kesimpulan (kriteria DILIrank "ada sinyal apa pun" vs kriteria LiverTox "ada bukti klinis kuat"). Ini tidak akan hilang seiring waktu.
>
> **Gap yang ditemukan dari klarifikasi ini:** skema `hepatwin_compounds` saat ini **tidak membedakan** dua kondisi epistemik yang berbeda — "belum divalidasi" vs "sudah divalidasi dan memang tidak ada bukti" — keduanya sama-sama tersimpan sebagai `injury_pattern = "Tidak Terklasifikasi"`. Ini relevan langsung untuk `evidence_note` (§4.4 lanjutan di bawah): tanpa pembeda ini, `evidence_note` tidak bisa jujur menyebutkan yang mana. Lihat gerbang **K6**.

**Rekomendasi:** jangan "diperbaiki" dengan memaksa keduanya konsisten (itu akan mengarang data). Sebaliknya, sediakan field penjelas di respons agar frontend bisa menampilkan keterangan singkat — mis. `"Pola cedera spesifik tidak tersedia di monograf LiverTox; hotspot ditampilkan difus redup"`. Kejujuran lebih baik daripada konsistensi palsu.

> **Catatan tambahan soal timing:** karena kurasi LiverTox oleh Farmasi berjalan **paralel** dan aktif berubah, `injury_pattern` untuk sebagian senyawa bisa berubah di antara waktu F1 dijalankan dan waktu F9 (laporan akhir) ditulis. Ini bukan masalah selama disadari — F1 wajib mencatat **tanggal/waktu snapshot data** secara eksplisit (lihat F1 langkah tambahan di `EXECUTION_PLAN_FUSION.md`), supaya laporan tidak diam-diam jadi usang tanpa disadari.

---

## 5. Batas Lingkup (Scope Guard)

Agent **tidak boleh** mengerjakan hal berikut. Bila muncul dorongan ke arah ini, catat di `reports/backlog_fusion.md` lalu lanjutkan:

- **Mengubah skema kalibrasi** (`calibrate.py`, `calibrator_gatnn_dnn.pkl`) — Ketua Tim sudah memutuskan dipakai apa adanya. Perbaikan §3.1 dilakukan di lapisan fusi, bukan di kalibrasi.
- **Melatih ulang atau mengubah bobot model** (`model_gatnn_dnn.pt`)
- Mengubah `pbpk_engine.py`, `allometric_service.py` — sudah lulus audit
- Mengubah pipeline `ml/` (C1–C12 sudah selesai)
- Mengubah logika autocomplete / `compound_repository.py`
- Menambahkan machine learning apa pun ke lapisan fusi — D9 secara eksplisit mensyaratkan **rule-based**
- Mengarang `injury_pattern` untuk 824 senyawa "Tidak Terklasifikasi"
- Mengubah frontend / React Three Fiber (Alur E)

---

## 6. Gerbang Keputusan Manusia

Agent **tidak boleh menebak**. Bila belum ada keputusan, pakai default, tandai `[KEPUTUSAN AI — PENDING REVIEW]`, lanjutkan.

| ID | Pertanyaan | Ke siapa | Default sementara | Memblokir |
|---|---|---|---|---|
| **K1** | Setuju mengganti rantai `or` jadi matriks 3×3 (§4.1)? | Ketua Tim | Ya — matriks, karena lebih setia pada tabel PRD | F3 |
| **K2** | Nilai final `T_low` & `T_high` (§4.2) | Farmasi + Ketua Tim | Metode (b) pemetaan-balik: T_low ≈ 0.5458, T_high ≈ 0.6866 | F3 |
| **K3** | Enam ambang paparan (30/10 mg/kg, 0.40/0.35/0.30/0.20) — dipertahankan, direvisi, atau diberi sitasi? | Farmasi | Dipertahankan, ditandai sebagai asumsi desain | F5 |
| **K4** | Field baru di `SimulationResponse` (intensitas, mode, catatan bukti) | Ketua Tim + Vedo | Usulan di `EXECUTION_PLAN_FUSION.md` F7 | F7 |
| **K5** | Ganti nama `threshold_line_used` agar akurat (§3.4)? | Ketua Tim | Ya — jadi `absolute_concentration_threshold_used` | F5 |
| **K6** *(baru)* | Tambah field status kurasi (mis. `curation_status: "validated" \| "pending_review"`) di `hepatwin_compounds`, supaya `evidence_note` bisa jujur bedakan "belum dicek" vs "sudah dicek, tidak ada bukti"? | Ketua Tim + Farmasi | **Tidak** — di luar cakupan branch `fusion` (perubahan skema DB, bukan lapisan fusi). `evidence_note` sementara pakai kalimat netral yang tidak mengklaim salah satu kondisi | Tidak memblokir F4, tapi membatasi presisi `evidence_note` |

---

## 7. Definition of Done (Tingkat Proyek)

- [ ] Branch `fusion` ada, bercabang dari `master`, `master` tidak berubah
- [ ] **Hijau terbukti bisa muncul** untuk senyawa yang memang aman (memperbaiki §3.1)
- [ ] **`MODERATE_EXPOSURE` terbukti berpengaruh** pada setidaknya satu kombinasi (memperbaiki §3.2)
- [ ] Ketiga warna terpakai pada katalog 1.231 senyawa — distribusinya dilaporkan
- [ ] Uji senyawa acuan lulus: parasetamol MERAH, ada senyawa aman yang HIJAU
- [ ] `hotspot_base_intensity` diteruskan ke respons (memperbaiki §3.3)
- [ ] Instrumentasi latensi terpasang; **p95 end-to-end < 5 detik terbukti dengan angka**, bukan diklaim
- [ ] Paralelisme AI‖PBPK terverifikasi nyata (bukan berurutan menyamar asinkron)
- [ ] Fusi tetap 100% rule-based — tidak ada ML tambahan
- [ ] Hanya senyawa `is_simulatable = TRUE` yang diproses — dibuktikan lewat test
- [ ] Enam ambang paparan ditandai sebagai asumsi desain, bukan klaim berbasis literatur
- [ ] Seluruh `pytest` hijau, tidak ada regresi terhadap test `master`

---

## 8. Prinsip Kerja (Wajib Dipatuhi Agent)

1. **Jangan mengarang angka.** Setiap distribusi, latensi, atau metrik dari eksekusi nyata.
2. **Kegagalan adalah keluaran yang sah.** Bila latensi ternyata > 5 detik, laporkan apa adanya — jangan diakali dengan mematikan SHAP diam-diam.
3. **Bedakan keputusan tim vs keputusan AI.** Tandai `[KEPUTUSAN AI — PENDING REVIEW]`.
4. **Satu task = satu commit**, format `F<n>: <ringkasan>`.
5. **Berhenti di gerbang K1–K5.**
6. **Jangan melebarkan cakupan** (§5).
7. **`master` baca-saja.** Merge adalah keputusan terpisah Ketua Tim.
8. **Jangan pernah commit `.env` atau kunci Supabase.**
9. **Jangan mengubah kalibrasi** untuk memperbaiki §3.1 — itu keputusan yang sudah dibekukan Ketua Tim.

---

## 9. Referensi

- `HepaTwin_PRD.md` v2.0 — Bab 6.3 (FR-05), Bab 7.1 (arsitektur paralel), **Bab 8.3 (logika fusi — sumber utama D9)**, Bab 9 (UC-02)
- `Dokumen_Kerja_Internal.docx` — Alur Kerja D, task D7 & D9
- `PBPK_Engine_Audit_Report.md` — audit mesin PBPK (lulus; keterbatasan cakupannya dijelaskan di §2)
- `PROJECT_FIX_MODEL.md` & `ml/reports/C7_evaluasi.md` — asal-usul `dili_score` dan temuan kalibrasi
- Soejima et al. (2022); Ghabril et al. (2025) — dasar faktor modifikator usia & BMI (**bukan** dasar nilai ambangnya)
