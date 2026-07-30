# EXECUTION_PLAN_UPSCALE.md — Rencana Eksekusi Agent

**Proyek:** HepaTwin — Mesin B (AI/ML) Upscale
**Repo:** `hepatwin-backend-py` (repo yang sudah ada — **bukan** repo baru)
**Branch:** `upscale`, dibuat dari `master`. Seluruh task di bawah ini adalah commit di branch `upscale`. `master` tidak disentuh.
**Dokumen induk:** `UPSCALE.md` v2.1 — baca lebih dulu
**Versi:** 2.1 — revisi struktur kerja: branch baru di repo yang sudah ada, bukan repo terpisah

---

## Ringkasan Perubahan dari v2.0 → v2.1

| Bagian | Perubahan |
|---|---|
| TU.0 | Ditulis ulang total: **buat branch**, bukan buat repo. Struktur `ml/` ditambahkan berdampingan dengan `app/` yang sudah ada |
| Aturan Main #8 | Direvisi: `master` (bukan "repo lama") bersifat baca-saja selama pengerjaan |
| TU.14 | Ditegaskan: langkah terakhirnya adalah menyalin artefak dari `ml/models/` ke `app/models/`, karena sekarang satu repo yang sama |
| Seluruh path task | Diberi prefix `ml/` untuk kode pipeline riset, membedakan dari `app/` yang merupakan runtime |

## Ringkasan Perubahan dari v1.0 → v2.0 (tetap berlaku)

| Task | Perubahan |
|---|---|
| TU.3 | Blocker B1 (pilih skema Arm B) **selesai** — Arm B sudah final = DILIrank+LiverTox |
| TU.5 | Temporal split turun status dari wajib → opsional |
| TU.12 | Ditulis ulang total: bangun LiverTox, bukan DILIst |
| TU.13 | Tabel perbandingan tanpa kolom L3 |
| TU.16, TU.17 | Tox21 multi-task & FAERS signal, keduanya stretch, tidak memblokir apa pun |

---

## Aturan Main untuk Agent (revisi #8)

1. Kerjakan berurutan sesuai dependensi.
2. Satu task = satu commit, format `TU.<n>: <ringkasan>`, di branch `upscale`.
3. Berhenti di gerbang 🔴 `BLOCKED` — laporkan, jangan menebak.
4. Jangan mengarang angka — semua angka berasal dari eksekusi nyata.
5. Kegagalan itu keluaran yang sah — catat apa adanya.
6. Jangan melebarkan cakupan (`UPSCALE.md` §12).
7. Windows path: forward slash atau prefix `r"..."`.
8. **`master` bersifat baca-saja selama pengerjaan TU.0–TU.17.** Jangan commit ke `master`, jangan merge `upscale` ke `master` — itu keputusan terpisah ketua tim setelah review. Boleh menarik perubahan **dari** `master` **ke** `upscale` bila ada update lain (mis. dari frontend), tidak sebaliknya.
9. Kode di `app/` (runtime FastAPI yang sudah ada) diedit di tempat, bukan ditulis ulang dari nol — lihat `UPSCALE.md` §9 untuk pembagian `app/` vs `ml/`.

---

## Peta Task (revisi)

| ID | Task | Status Gerbang | Perkiraan |
|---|---|---|---|
| TU.0 | Bootstrap branch `upscale` + struktur `ml/` | — | 1 jam |
| TU.1 | Unduh & inspeksi DILIrank 2.0 | — | 1 jam |
| TU.2 | Resolusi SMILES + standardisasi (DILIrank) | — | 4–8 jam |
| TU.3 | Harmonisasi label DILIrank | 🔴 B2, B3 | 2 jam |
| TU.4 | Bangun dataset Arm A | — | 2 jam |
| TU.5 | Modul split (random/scaffold; temporal opsional) | — | 2 jam |
| TU.6 | Featurizer (graf + fingerprint + SMARTS) | 🟡 B4 | 4 jam |
| TU.7 | Arsitektur GATNN-DNN | — | 3 jam |
| TU.8 | Training loop + baseline | — | 4 jam |
| TU.9 | Evaluasi L1/L2 Arm A × 5 seed | — | 3 jam |
| TU.10 | Kalibrasi | — | 2 jam |
| TU.11 | Explainability | 🔴 B5 | 4 jam |
| **TU.12** | **Bangun dataset Arm B (LiverTox + DILIrank)** | — (tidak lagi blocked) | 4–6 jam |
| TU.13 | Jalankan Arm B + tabel perbandingan | — | 3 jam |
| TU.14 | Integrasi backend + kontrak API | — | 4 jam |
| TU.15 | Laporan akhir & limitations | — | 3 jam |
| TU.16 | *(stretch)* Tox21 multi-task auxiliary head | — | 4–6 jam |
| TU.17 | *(stretch)* FAERS disproportionality signal | — | 4–6 jam |

**Jalur tidak terblokir yang bisa langsung dikerjakan:** TU.0 → TU.1 → TU.2 → TU.4 → TU.5 → TU.7 → TU.8 → **TU.12** (Arm B sekarang juga bisa langsung jalan, tidak menunggu keputusan manusia). Gerbang manusia hanya menggigit di TU.3, TU.6 (sebagian), dan TU.11.

---

## TU.0 — Bootstrap Branch `upscale` (DITULIS ULANG — sebelumnya "bootstrap repo baru")

**Tujuan:** siapkan branch dan struktur `ml/` di dalam repo `hepatwin-backend-py` yang sudah ada, tanpa mengganggu `app/` yang sedang berjalan.

**Langkah:**
1. `git checkout master && git pull` — pastikan mulai dari `master` terbaru.
2. `git checkout -b upscale` — buat branch baru.
3. Buat struktur `ml/` **berdampingan** dengan `app/` yang sudah ada, persis seperti `UPSCALE.md` §9:
   ```
   ml/{configs,data/{raw,interim,processed},src/hepatwin_ml/{data,features,models,stretch},scripts,reports,models}
   ```
4. **Jangan sentuh isi `app/` di task ini.** Perubahan pada `app/` baru terjadi di TU.14.
5. Tulis `ml/requirements.txt` (isi identik dengan yang tercantum di v1.0 — torch, torch-geometric, rdkit, pandas, scikit-learn, pubchempy, pyyaml, shap, matplotlib, tqdm, pytest), lalu gabungkan ke `requirements.txt` di root repo supaya satu environment mencakup keduanya.
6. Tambahkan ke `.gitignore` di root (bukan file baru — edit yang sudah ada): `ml/data/raw/`, `ml/data/interim/`, `ml/models/*.pt`, `__pycache__/`, `.venv/`.
7. Salin `UPSCALE.md` dan `EXECUTION_PLAN_UPSCALE.md` ke root repo.
8. Beri komentar penanda obsolete di `data_preparation/deduplicate_smiles.py` (lihat `UPSCALE.md` §9) — **jangan dihapus**, itu jejak keputusan desain yang berubah.
9. Commit pertama: `TU.0: bootstrap branch upscale, tambah struktur ml/`.

**Acceptance criteria:**
- [ ] Branch `upscale` ada dan aktif, `git log` menunjukkan ia bercabang dari commit terbaru `master`
- [ ] `app/` tidak ada perubahan sama sekali di commit ini — verifikasi dengan `git diff master upscale -- app/` kosong
- [ ] `pip install -r requirements.txt` berhasil untuk gabungan dependency `app/` + `ml/`
- [ ] `python -c "import torch_geometric, rdkit, pubchempy"` tidak error

---

## TU.1 — TU.11: isi tidak berubah dari v1.0, path diberi prefix `ml/`

Jalankan persis seperti spesifikasi v1.0 (resolusi PubChem di TU.2, harmonisasi label dengan blocker B2/B3 di TU.3, arsitektur GATNN-DNN 34-dim node / 6-dim edge / logit output di TU.7, training loop 5-seed di TU.8, kalibrasi isotonic di TU.10, explainability SHAP ter-batch pada `SMARTS_SLICE` di TU.11) — **satu-satunya perubahan mekanis:** setiap path yang dulu ditulis `src/...`, `data/...`, `reports/...`, `configs/...`, `models/...` sekarang dibaca sebagai `ml/src/...`, `ml/data/...`, `ml/reports/...`, `ml/configs/...`, `ml/models/...`. Isi logika, acceptance criteria, dan urutan task **tidak berubah**.

Satu penyesuaian isi (bukan cuma path) di **TU.5**:

### TU.5 (revisi) — Modul Split

**File:** `ml/src/hepatwin_ml/data/splits.py`

1. `random_kfold(df, k=5, seed)` — wajib
2. `scaffold_kfold(df, k=5, seed)` — wajib, satu scaffold tidak boleh muncul di dua fold
3. `temporal_split(df)` — **implementasikan tetap**, tapi beri flag `optional=True` di config. Tidak masuk kriteria Definition of Done. Berguna sebagai analisis tambahan di laporan akhir (§4.3 `UPSCALE.md`), bukan syarat kelulusan.

**Acceptance criteria (revisi):**
- [ ] `pytest ml/tests/test_splits.py` hijau untuk random & scaffold
- [ ] Temporal split tetap ada di kode, ditandai eksplisit "opsional" di docstring
- [ ] `ml/reports/04_split_stats.md` — cukup random & scaffold; temporal dilaporkan terpisah bila sempat dijalankan

---

## TU.12 — Bangun Dataset Arm B: DILIrank 2.0 + LiverTox (DITULIS ULANG)

**Tujuan:** dataset gabungan sesuai silsilah Yang et al. (2024) / Wibowo et al. (2025), sesuai arahan ketua tim.

**Tidak lagi diblokir keputusan manusia** — skema sudah final di `UPSCALE.md` §3.3.

**File:** `ml/src/hepatwin_ml/data/build_livertox.py`, revisi `build_dataset.py`

### Langkah

1. **Unduh Master List of LiverTox Drugs** (spreadsheet Excel resmi NIDDK/NLM) → `ml/data/raw/livertox_master_list.xlsx`.
2. **Inspeksi kolom** (ulangi pola TU.1): cetak nama kolom persis, `value_counts()` untuk kolom Likelihood Score. Verifikasi nilai yang benar-benar muncul (`A`, `B`, `C`, `D`, `E`, `E*`, `X` — atau variasi penulisan lain, mis. `E *` dengan spasi). **Jangan asumsikan format string tanpa mengecek langsung.**
3. **Binerisasi:**
   ```yaml
   livertox_AB_vs_EEstar:
     A: 1
     B: 1
     C: null      # dibuang
     D: null      # dibuang
     "E": 0
     "E*": 0
     X: null       # dibuang
   ```
4. **Resolusi SMILES** untuk nama obat LiverTox — **pakai ulang cache PubChem dari TU.2** (banyak nama akan tumpang tindih dengan DILIrank, jadi cache mengurangi jumlah API call signifikan).
5. **Standardisasi** — pakai ulang pipeline `standardize.py` dari TU.2 apa adanya.
6. **Gabungkan dengan Arm A** (hasil TU.4) via `inchikey`:
   - Buat kolom `in_dilirank: bool`, `in_livertox: bool`
   - Untuk senyawa yang muncul di **keduanya** dengan label sama → satu baris, `source_dataset = "both"`
   - Untuk yang muncul di keduanya dengan label **berbeda** → **DILIrank menang**, catat baris ini secara terpisah ke `ml/reports/06_label_conflicts.csv` untuk transparansi (jangan hanya menimpa diam-diam)
   - Untuk yang hanya di LiverTox → `source_dataset = "livertox_only"`

**Keluaran:** `ml/data/processed/arm_b.parquet`, kolom sama seperti `arm_a.parquet` ditambah `source_dataset`.

**Laporan wajib** → `ml/reports/06_arm_b_construction.md`, wajib memuat:

| Tahap | Jumlah |
|---|---|
| DILIrank setelah TU.4 | ? |
| LiverTox mentah (Master List) | ? |
| LiverTox setelah binerisasi (buang C/D/X) | ? |
| LiverTox setelah resolusi SMILES | ? |
| Overlap InChIKey dengan DILIrank | ? |
| **Konflik label pada overlap** | ? |
| **Total Arm B final** | ? |

**Acceptance criteria:**
- [ ] `ml/data/processed/arm_b.parquet` ada
- [ ] Tingkat konflik label terhitung dan dilaporkan sebagai angka nyata (bukan "sedikit"/"jarang" — angka pasti)
- [ ] Ukuran Arm B dibandingkan terhadap ekspektasi 1.600–1.900 di `UPSCALE.md` §3.3 — bila melenceng jauh, selidiki sebelum lanjut ke training
- [ ] Parasetamol dan amoxicillin-clavulanate diverifikasi manual ada di Arm B dengan label yang masuk akal

🚩 **Jangan langsung lanjut ke TU.13 bila tingkat konflik label > 15%.** Itu tanda ada masalah di resolusi SMILES atau standardisasi (mis. garam vs bentuk bebas dihitung sebagai senyawa berbeda), bukan tanda dataset yang genuinely kontroversial secara farmakologis. Audit dulu.

---

## TU.13 — Jalankan Arm B + Tabel Perbandingan (revisi ringan)

**File:** `scripts/compare_arms.py`

1. Ulangi TU.8–TU.10 untuk Arm B, hyperparameter & seed identik dengan Arm A.
2. Tabel perbandingan (kolom L3 dihapus dari v1.0):

   | Arm | n | L1 AUC (mean±std) | L2 AUC (mean±std) | MCC | Brier | ECE |
   |---|---|---|---|---|---|---|
   | A — DILIrank saja | ? | ? | ? | ? | ? | ? |
   | B — DILIrank+LiverTox | ? | ? | ? | ? | ? | ? |
   | *(pembanding)* Wibowo et al. 2025 | 1573 | 0.757 | — | 0.399 | — | — |

3. DeLong test pada AUC L1 antara Arm A dan Arm B.
4. Tulis kesimpulan berbasis angka.

**Acceptance criteria:**
- [ ] `ml/reports/07_comparison.md` ada, termasuk baris pembanding Wibowo et al.
- [ ] Kesimpulan eksplisit: Arm B lebih baik / Arm A lebih baik / tidak berbeda signifikan
- [ ] Bila Arm B AUC L1 jauh dari band 0,74–0,80 (`UPSCALE.md` §8) → audit dulu, jangan langsung dilaporkan sebagai temuan final

---

## TU.14 — Integrasi Backend (disederhanakan — sekarang satu repo, satu branch)

**Perubahan dari v1.0:** dulu task ini berarti memindahkan kode antar-repo. Sekarang `app/` dan `ml/` sudah berada di branch yang sama, jadi integrasinya tinggal edit-di-tempat + commit, tanpa proses salin-antar-repo.

**Langkah:**
1. `python ml/scripts/export_to_app.py` — salin `ml/models/model_arm_a.pt` (atau `model_arm_b.pt`, tergantung mana yang dipakai produksi) beserta kalibratornya ke `app/models/`. Script ini juga menyalin `SMARTS_SLICE` dan daftar SMARTS final ke lokasi yang dibaca `app/services/ai_engine.py`.
2. Tulis ulang `app/services/ai_engine.py` **di tempat** (bukan file baru) untuk memuat artefak GATNN-DNN + kalibrator dari `app/models/`.
3. 🔴 **Hapus perilaku silent fallback.** Bila artefak tidak ada / gagal dimuat → `HTTPException(503)` dengan pesan eksplisit. Dilarang mengembalikan `0.5`.
4. Tambahkan field baru ke `SimulationResponse` di `app/models/schemas.py`: `model_version`, `model_status`, `score_is_calibrated`, `internal_cv_auc` (bukan `external_auc` — lihat `UPSCALE.md` §10).
5. Perbaiki juga: global exception handler yang membocorkan string error mentah ke klien → ganti pesan generik + logging sisi server.
6. Benchmark end-to-end Mode Triase Umum di branch `upscale`.

**Acceptance criteria:**
- [ ] `git diff master upscale -- app/` menunjukkan perubahan yang jelas dan terbatas pada `ai_engine.py`, `schemas.py`, exception handler — bukan bongkar struktur `app/`
- [ ] Test: hapus file model di `app/models/` → endpoint balas 503, **bukan** 200 dengan skor 0,5
- [ ] Latensi end-to-end < 5 detik (p95)
- [ ] Response berisi seluruh field baru
- [ ] Tidak ada string exception mentah di response body

---

## TU.15: tidak berubah dari v2.0

Ikuti spesifikasi v2.0 apa adanya (path sudah diberi prefix `ml/` di atas), dengan tambahan wajib di `ml/reports/limitations.md`:

- **Alasan tidak ada external test** — dijelaskan sebagai keputusan yang konsisten dengan praktik nyata Wibowo et al. (2025), bukan sebagai kelalaian. Sertakan kutipan/rujukan §1 `UPSCALE.md`.
- **Status Tox21/FAERS** — jelaskan apakah TU.16/TU.17 sempat dikerjakan atau tidak, dan kalau tidak, nyatakan itu sebagai batasan waktu, bukan disembunyikan.

---

## TU.16 — *(Stretch, opsional)* Tox21 Multi-Task Auxiliary Head

**Tidak memblokir apa pun. Kerjakan hanya bila TU.0–TU.15 sudah selesai dan masih ada waktu.**

**Tujuan:** memakai Tox21 sebagai sinyal tambahan tanpa mencemari label DILI, sesuai keinginan ketua tim untuk "menggunakan" Tox21.

**Langkah:**
1. Unduh Tox21 (tersedia via MoleculeNet/DeepChem atau PubChem BioAssay), 12 kolom label assay.
2. Tambahkan **head keluaran kedua** ke `HybridGNN`: dari representasi graf 256-dim yang sama, cabang linear terpisah memprediksi 12 label Tox21 (multi-label, `BCEWithLogitsLoss` per kolom, mengabaikan `NaN`).
3. Training gabungan: `loss_total = loss_dili + λ * loss_tox21`, mulai `λ = 0.1`, tuning bila ada waktu.
4. Bandingkan AUC DILI dengan/tanpa auxiliary head. Laporkan sebagai eksperimen tambahan terpisah dari tabel utama TU.13, **jangan dicampur** ke perbandingan Arm A vs Arm B.

**Acceptance criteria:**
- [ ] `ml/reports/08_tox21_ablation.md` — AUC DILI dengan vs tanpa auxiliary head
- [ ] Diberi label jelas sebagai eksperimen tambahan, tidak menggantikan Arm A/B manapun

---

## TU.17 — *(Stretch, opsional)* FAERS Disproportionality Signal

**Tidak memblokir apa pun.**

**Tujuan:** turunkan satu skor per obat dari FAERS untuk dipakai sebagai fitur tambahan, sesuai keinginan ketua tim untuk "menggunakan" FAERS.

**Langkah:**
1. Unduh FAERS quarterly data (tabel `DEMO`, `DRUG`, `REAC`) untuk beberapa kuartal terbaru yang tersedia.
2. Untuk setiap obat di Arm B, hitung **Reporting Odds Ratio (ROR)** terhadap istilah MedDRA yang relevan dengan hepatotoksisitas (mis. "Hepatic failure", "Hepatitis", "Jaundice", "Liver injury" — daftar lengkap wajib ditinjau anggota Farmasi sebelum dipakai, sama seperti daftar SMARTS).
3. Normalisasi skor (log-ROR, clip outlier), lekatkan sebagai **1 kolom tambahan** di vektor DNN (bukan di training set sebagai label baru).
4. Latih ulang Arm B dengan fitur tambahan ini, bandingkan AUC.

**Acceptance criteria:**
- [ ] `ml/reports/09_faers_feature_ablation.md`
- [ ] Daftar istilah MedDRA yang dipakai dicatat eksplisit dan ditandai `# PENDING pharmacy review`
- [ ] Jelas dilabeli sebagai eksperimen fitur tambahan, bukan Arm C baru

---

## Ringkasan Gerbang Manusia (revisi)

| Gerbang | Pertanyaan | Ke siapa | Memblokir | Status |
|---|---|---|---|---|
| **B2** | vLess-DILI-concern → positif atau dibuang? | Farmasi | TU.3 | 🤖 Di-bypass sementara oleh AI — lihat §14.1 |
| **B3** | Amox-clav ada di kelas mana? Ikut terbuang? | Farmasi | TU.3 | ✅ Tidak relevan untuk Arm A — lihat §14.1 (temuan data, bukan bypass) |
| **B4** | SMILES amox-clav: pecah atau ambil fragmen utama? | Farmasi + AI/ML | TU.6 | 🤖 Di-bypass sementara oleh AI — lihat §14.1 |
| **B5** | Daftar & penamaan SMARTS final | Farmasi | TU.11 | 🤖 Akan di-bypass sementara oleh AI saat TU.11 dikerjakan — lihat §14.1 |
| **B6** *(baru, hanya untuk TU.17)* | Daftar istilah MedDRA hepatotoksisitas untuk FAERS | Farmasi | TU.17 saja, tidak memblokir apa pun di jalur utama | Belum dikerjakan (stretch) |

~~B1~~ **selesai** — Arm B sudah final = DILIrank + LiverTox, tidak lagi menunggu keputusan.

Dibanding v1.0: jalur utama (TU.0–TU.15) sekarang jauh lebih sedikit terblokir. Hanya TU.3 dan TU.11 yang benar-benar menunggu manusia; TU.6 sebagian (B4 memengaruhi featurisasi amox-clav, tapi tidak menghentikan seluruh task).

---

## §14.1 — Kebijakan Bypass Gerbang Manusia oleh AI (ditambahkan 2026-07-31)

**Konteks:** Atas instruksi pemilik repo, gerbang B2/B3/B4/B5 di-bypass agar pipeline TU.1–TU.17 bisa berjalan tanpa menunggu jadwal review anggota Farmasi. **Ini bukan pengganti validasi Farmasi** — Definition of Done (§11 UPSCALE.md) tetap mensyaratkan tanda tangan Farmasi untuk daftar SMARTS dan skema label sebelum rilis final. Keputusan di bawah ini berstatus **sementara/provisional**, harus ditinjau ulang sebelum dianggap final, dan **wajib ditandai jelas di setiap laporan (`ml/reports/*.md`) yang memakainya** dengan label `[KEPUTUSAN AI — PENDING REVIEW FARMASI]`.

| Gerbang | Keputusan sementara AI | Dasar | Perlu dikonfirmasi Farmasi karena |
|---|---|---|---|
| **B2** | `vMost-DILI-concern` + `vLess-DILI-concern` = label positif (1), `vNo-DILI-concern` = negatif (0), `Ambiguous-DILI-concern` dibuang | Ini memang sudah jadi default yang tertulis di UPSCALE.md §3.2 sejak v1.0 ("sama seperti v1.0"), dan konsisten dengan skema yang dipakai literatur DILI-ML yang jadi rujukan arsitektur (Yang et al. 2024, Wibowo et al. 2025) | vLess mencampur senyawa dengan bukti hepatotoksisitas lemah/tidak konklusif — signifikansi klinis vs. label FDA aktual perlu dinilai oleh yang paham farmakovigilans, bukan cuma preseden literatur. **Bukti konkret baru (TU.12, `06_arm_b_construction.md` §Audit):** dari 76 konflik label DILIrank×LiverTox pada senyawa yang sama, 94,7% arahnya DILIrank-positif/LiverTox-negatif — indikasi `vLess` sistematis lebih longgar dari kriteria klinis LiverTox, bukan cuma kekhawatiran teoretis |
| **B3** | Tidak ada keputusan yang diperlukan untuk Arm A — DILIrank 2.0 tidak memuat entri kombinasi amoxicillin-clavulanate sama sekali (diverifikasi langsung: 0 baris cocok pola `clavulan`, lihat `ml/reports/01_dilirank_inspection.md`). Pertanyaan ini baru relevan lagi di TU.12 (Arm B, lewat LiverTox) | Temuan data langsung, bukan judgment call | Saat amox-clav muncul via LiverTox di Arm B, klasifikasi & keikutsertaannya tetap perlu ditinjau Farmasi |
| **B4** | ~~Kedua fragmen~~ **REVISI (2026-07-31):** ambil **fragmen utama** saja, mengikuti perilaku `standardize.py` yang direuse dari `dev-vedo` (`LargestFragmentChooser` + `check_eligibility` menolak SMILES bercampur/`.` secara eksplisit — `MixtureError`). Representasi multi-komponen tidak kompatibel dengan pipeline standardisasi yang sudah teruji & dipakai bersama runtime `app/`, jadi opsi itu dibatalkan | Konsistensi dengan kode standardisasi yang sama dipakai TU.2 (DILIrank) dan runtime validasi SMILES (`standardize_or_raise`) — mengubah perilaku itu berisiko merusak jalur yang sudah teruji, demi satu senyawa kombinasi | Fragmen mana yang otomatis terpilih sebagai "utama" (kemungkinan besar amoxicillin, MW lebih besar) belum tentu fragmen yang secara farmakologis bertanggung jawab atas sinyal DILI (literatur justru sering mengaitkan hepatotoksisitas Augmentin ke clavulanate) — perlu ditinjau Farmasi apakah ini dapat diterima atau perlu penanganan khusus di luar pipeline standar |
| **B5** | Belum diputuskan — akan memakai daftar SMARTS/toxicophore dari literatur DILI-SAR yang sudah dipublikasi (bukan daftar buatan sendiri) saat TU.11 dikerjakan, dengan penandaan `[KEPUTUSAN AI — PENDING REVIEW FARMASI]` di laporan explainability | Placeholder — belum ada keputusan konkret sampai TU.11 dimulai | Nama & interpretasi klinis tiap pola SMARTS wajib divalidasi sebelum dipakai di UI/laporan yang dilihat pengguna |

**Aturan turunan untuk seluruh task selanjutnya:** setiap kali TU.3, TU.6, atau TU.11 menghasilkan artefak yang bergantung pada keputusan di atas, file laporan terkait wajib mencantumkan baris:

```
> ⚠️ [KEPUTUSAN AI — PENDING REVIEW FARMASI]: <ringkasan keputusan spesifik + baris tabel di atas yang jadi rujukan>
```

Ini supaya siapa pun yang membaca laporan (termasuk ketua tim/Farmasi nanti) langsung tahu bagian mana yang masih perlu ditinjau, tanpa perlu membaca ulang dokumen ini.
