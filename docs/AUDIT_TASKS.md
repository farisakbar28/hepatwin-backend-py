# AUDIT_TASKS.md — Rekonsiliasi Repo `dev-vedo` + Perbaikan Terarah

**Dibaca setelah** `AGENTS.md` dan **sebelum** melanjutkan `EXECUTION_PLAN.md`.
**Konteks:** repo backend sudah dibuat lebih dulu oleh anggota tim, dengan struktur folder yang berbeda dari cetak biru `EXECUTION_PLAN.md`, dan mengandung beberapa nilai yang belum tervalidasi. File ini mengatasi keduanya dalam satu urutan yang aman, tanpa membangun ulang dari nol.

**Prinsip kerja di file ini:** perbaiki di tempat (`git mv` bila perlu pindah path), pertahankan logika yang sudah benar, jangan menulis ulang arsitektur yang sudah sesuai PRD hanya demi kerapian kosmetik.

---

## BAGIAN 0 — STATUS T0.1 DAN PEMETAAN STRUKTUR

### Status T0.1 (EXECUTION_PLAN.md)

```
Status : DONE (dengan catatan)
Catatan: Struktur folder repo berbeda dari cetak biru Arsitektur §B.3.
         Direkonsiliasi lewat tabel pemetaan di bawah, BUKAN dengan
         memindahkan seluruh file ke struktur cetak biru.
```

Repo ini **tidak memakai** prefiks folder `backend/` — `app/` ada langsung di root repo. Ini repo backend itu sendiri (terpisah dari repo `ml/`), jadi ini bukan penyimpangan yang perlu diperbaiki, cuma perlu didokumentasikan supaya task berikutnya tidak salah alamat.

### Tabel pemetaan path — WAJIB dibaca sebelum eksekusi task manapun di `EXECUTION_PLAN.md`

Saat `EXECUTION_PLAN.md` menyebut path di kolom kiri, path yang benar di repo ini adalah kolom kanan.

| Path di EXECUTION_PLAN.md | Path aktual di repo ini | Status |
|---|---|---|
| `backend/app/main.py` | `app/main.py` | Ada, perlu perbaikan (TA.5) |
| `backend/app/api/schemas.py` | `app/models/schemas.py` | Ada, perlu rekonsiliasi field (TA.4) |
| `backend/app/api/routes_health.py` | `app/api/endpoints/health.py` | Ada |
| `backend/app/api/routes_simulate.py` | `app/api/endpoints/simulation.py` | Ada |
| `backend/app/api/routes_compounds.py` | — | **Belum ada** (lihat TA.7) |
| `backend/app/api/routes_model_info.py` | — | Belum ada, dijadwalkan T1.17 |
| `backend/app/engines/pkpd/*.py` (4 file terpisah) | `app/services/pkpd_engine.py` (1 file gabungan) | Ada, perlu perbaikan (TA.1) |
| `backend/app/engines/ml/predictor.py` | `app/services/ai_engine.py` + `app/services/simulation_orchestrator.py` | Ada, perlu perbaikan (TA.2, TA.3) |
| `backend/app/chem/standardize.py` | — | Belum ada sebagai modul terpisah, logika ada di `ai_engine.py` fungsi `smiles_to_graph_and_features` |
| `backend/app/chem/smarts_library.py` | `SMARTS_PATTERNS` di dalam `app/services/ai_engine.py` | Ada, perlu dipisah + gerbang validasi (TA.2) |
| `backend/app/chem/features.py` | Tergabung di `ai_engine.py` | Ada, cukup dulu, jangan dipisah sekarang (lihat TA.0.1) |
| `backend/app/core/cache.py` | — | **Belum ada** (lihat TA.6) |
| `backend/app/core/errors.py` | — | **Belum ada**, saat ini `main.py` pakai exception handler generik yang bocor (TA.5) |
| `backend/app/core/registry.py` | — | Belum ada, dijadwalkan bersama T1.13 |
| `backend/requirements.txt` (inference-only) | `requirements.txt` (di root, sudah minimal) | Ada, sudah cukup ramping |

### TA.0.1 — Keputusan yang sudah diambil, jangan ditinjau ulang tiap sesi

Supaya tidak ada agent yang membuka diskusi ulang soal restrukturisasi folder di setiap sesi kerja:

1. **Struktur flat (`app/services/`, bukan `app/engines/{pkpd,ml}/`) dipertahankan.** Tidak ada nilai cukup besar untuk memaksa migrasi struktur folder sekarang. Refactor besar berisiko lebih tinggi daripada manfaatnya menjelang tenggat.
2. **`app/chem/` sebagai modul terpisah TIDAK dibuat di audit ini.** Fungsi chem masih boleh tinggal di dalam `ai_engine.py` untuk saat ini — asal dipisah dari class `HybridAIEngine` menjadi fungsi-fungsi modul-level yang bisa diimpor bersih (lihat TA.2). Pemisahan penuh ke file sendiri bisa menyusul di Sprint 1 saat pipeline training dibuat, bukan sekarang.
3. Task-task di `EXECUTION_PLAN.md` yang menyebut path `backend/app/...` **tetap dibaca isinya**, hanya path filenya yang disesuaikan lewat tabel di atas.

---

## BAGIAN 1 — TEMUAN AUDIT (urut berdasarkan tingkat risiko)

| # | Temuan | File | Tingkat risiko |
|---|---|---|---|
| F1 | Model GNN berjalan dengan **bobot random** (file `models/model.pt` tidak ada), tanpa penanda ke pengguna | `app/services/ai_engine.py` | **KRITIS** |
| F2 | Konstanta PD diisi angka asumsi (`K_IN=1.0`, `K_GSH=2.0`, dst.), bukan hasil validasi Farmasi | `app/services/pkpd_engine.py` | **KRITIS** |
| F3 | Garis nomogram pakai formula placeholder yang diaku sendiri di komentar sebagai sementara | `app/services/pkpd_engine.py` | **KRITIS** |
| F4 | Nama gugus SMARTS (`"Beta-lactam ring"`, dst.) tampil ke pengguna tanpa validasi Farmasi | `app/services/ai_engine.py` | TINGGI |
| F5 | Global exception handler mengembalikan `str(exc)` mentah ke client | `app/main.py` | TINGGI |
| F6 | Skema request/response belum memuat `engine`, `model_version`, `abstained` — tidak bisa dibedakan hasil mock/random dari hasil model terlatih | `app/models/schemas.py` | TINGGI |
| F7 | Endpoint `GET /api/v1/compounds` belum ada | — | SEDANG |
| F8 | Tidak ada folder `tests/` sama sekali | — | SEDANG |
| F9 | Nama field beda dari yang disepakati (`compound_id` vs `compound`, `smiles_string` vs `smiles`) — perlu keputusan, bukan langsung diubah | `app/models/schemas.py` | RENDAH (butuh keputusan) |

F1 dinaikkan sebagai temuan paling berisiko meskipun tidak eksplisit tercakup larangan di `AGENTS.md` — karena efeknya sama persis dengan F2/F3: sistem mengembalikan angka yang terlihat sah padahal tidak berdasar apa pun. **Tambahkan larangan baru ke `AGENTS.md` §3 setelah audit ini** (lihat TA.9).

---

## BAGIAN 2 — TASK PERBAIKAN

Urutan wajib. Jangan lompat. Setiap task = satu commit.

---

### TA.1 — Kosongkan konstanta PD, pasang gerbang `assert_ready()`

```
Status : DONE
Blokir : —
Dasar  : PRD §13 item #1 · AGENTS.md §3.1 · Arsitektur §C.3
File   : app/services/pkpd_engine.py
Temuan : F2, F3
```

**Langkah:**
1. Ganti `K_IN`, `K_ELIM`, `K_META`, `K_GSH`, `GSH_INITIAL`, `THETA_THRESHOLD` dari nilai float menjadi `None`, dibungkus struktur yang menyimpan status validasi (boleh reuse dataclass `PDConstant` dari Arsitektur §C.3, atau versi sederhana bila waktu sempit — yang penting ada field `validated_by_pharmacy: bool` dan `citation: str | None`)
2. Tambahkan fungsi `assert_ready()` di kelas `AcetaminophenPKPDEngine`, dipanggil di `__init__` atau sebelum `simulate_napqi_gsh_dynamics()` dan `get_nomogram_data()` dieksekusi
3. Hapus formula placeholder `rumack_line_200 = 200.0 * math.exp(-0.1 * t)` — ganti dengan pemanggilan fungsi yang juga digerbang oleh `assert_ready()`, bukan dihitung langsung dari konstanta bebas
4. F_ORAL, CL_SYSTEMIC, V1, KA, KE **TIDAK termasuk yang dikosongkan** — nilai-nilai itu sudah bersumber dari Morse et al. (2022) sesuai PRD §8.1 dan boleh tetap ada. Yang dikosongkan hanya konstanta hati/NAPQI/GSH dan parameter nomogram
5. Tambahkan docstring di setiap konstanta kosong: `# TODO(farmasi): lihat PRD §13 #1, menunggu balasan permintaan validasi`

**JANGAN:**
- Mengganti nilai kosong dengan angka lain yang "kelihatan masuk akal"
- Menghapus pemanggilan `assert_ready()` supaya server tetap bisa menyala untuk testing — buat mekanisme terpisah untuk itu (lihat TA.8), jangan lemahkan gerbangnya

**Selesai bila:**
- [ ] `grep -n "K_IN = \|K_ELIM = \|K_META = \|K_GSH = \|THETA_THRESHOLD = " app/services/pkpd_engine.py` tidak menampilkan baris dengan nilai numerik — semua `None`
- [ ] `grep -n "0.1 \* t\|200.0 \* math.exp" app/services/pkpd_engine.py` tidak ada hasil (placeholder nomogram terhapus)
- [ ] Memanggil `simulate_napqi_gsh_dynamics()` tanpa konstanta terisi → `RuntimeError` dengan pesan menyebut PRD §13 #1
- [ ] F_ORAL/CL_SYSTEMIC/V1/KA/KE tetap ada dan tidak berubah

---

### TA.2 — Pisahkan kamus SMARTS, pasang gerbang validasi Farmasi

```
Status : DONE
Blokir : —
Dasar  : PRD §8.5 · PRD §13 item #2 · AGENTS.md §3.7 · Arsitektur §D.2
File   : app/services/ai_engine.py
Temuan : F4
```

**Langkah:**
1. Pisahkan `SMARTS_PATTERNS` dari bagian atas `ai_engine.py` menjadi dua struktur:
   - `SMARTS_LIBRARY: dict[str, str]` — isinya tetap 9 pola yang sudah ada, tidak perlu ditambah/dikurangi sekarang
   - `SMARTS_VALIDATED_BY_PHARMACY: set[str] = set()` — **mulai kosong**
2. Tambahkan fungsi `validated_library() -> dict[str, str]` yang mengembalikan hanya anggota `SMARTS_LIBRARY` yang namanya ada di `SMARTS_VALIDATED_BY_PHARMACY`
3. Di method `get_explainability()`, filter `contributing_features` supaya **hanya nama dari `validated_library()`** yang boleh dikembalikan ke pengguna
4. Karena `validated_library()` kosong untuk saat ini, `get_explainability()` akan selalu mengembalikan list kosong atau pesan generik — itu hasil yang **benar**, bukan bug. Ganti fallback `"General structural features"` menjadi pesan yang jujur, misalnya `"Menunggu validasi Farmasi untuk gugus spesifik"`

**JANGAN:**
- Mengisi `SMARTS_VALIDATED_BY_PHARMACY` sendiri
- Menghapus pola dari `SMARTS_LIBRARY` — pola tetap dipakai sebagai fitur model, cuma tidak boleh ditampilkan namanya

**Selesai bila:**
- [ ] `get_explainability()` untuk SMILES apa pun tidak pernah mengembalikan nama gugus dari `SMARTS_LIBRARY` selama `SMARTS_VALIDATED_BY_PHARMACY` kosong
- [ ] Test: isi `SMARTS_VALIDATED_BY_PHARMACY` secara manual di test (bukan di kode produksi) dengan satu nama → nama itu muncul di output, yang lain tidak

---

### TA.3 — Tandai eksplisit bahwa model berjalan tanpa bobot terlatih

```
Status : DONE
Blokir : —
Dasar  : AGENTS.md §10 (anti-halusinasi, prinsip umum) · Arsitektur §D.1
File   : app/services/ai_engine.py, app/models/schemas.py, app/services/simulation_orchestrator.py
Temuan : F1 — TEMUAN PALING KRITIS
```

**Konteks:** `models/model.pt` tidak ada di repo. `HybridAIEngine.__init__` saat ini menangani kegagalan muat bobot dengan `logger.warning` lalu tetap jalan dengan bobot random — dan response API tidak membedakan ini dari hasil model terlatih.

**Langkah:**
1. Tambahkan atribut `self.weights_loaded: bool` di `HybridAIEngine`, diset `True` hanya bila `torch.load` berhasil, `False` bila fallback ke bobot random
2. Tambahkan properti `model_status` yang mengembalikan `"trained"` atau `"untrained_random_weights"`
3. Di `simulation_orchestrator.py`, sisipkan status ini ke response — minimal sebagai field baru sementara (lihat TA.4 untuk keputusan field final)
4. Di `endpoints/health.py`, `ai_ready` **jangan** hanya mengecek `getattr(orchestrator.ai_engine, 'ready', False)` (yang selalu `True` walau bobot random) — tambahkan pengecekan terpisah, misal `ai_weights_loaded`, supaya `/health` bisa membedakan "servernya nyala" dari "modelnya benar-benar terlatih"

**JANGAN:**
- Menghapus fallback bobot random itu sendiri — untuk development lokal itu berguna supaya server tetap bisa dites. Yang wajib diperbaiki adalah **transparansinya**, bukan perilakunya
- Membiarkan response API tetap tidak membedakan kedua kondisi ini setelah task ini selesai

**Selesai bila:**
- [x] `/health` mengembalikan field yang membedakan server nyala vs model benar-benar dimuat dari bobot terlatih
- [x] Response `/simulate` memuat penanda bahwa skor berasal dari bobot random (selama `model.pt` belum ada)
- [ ] Test: inisialisasi `HybridAIEngine` tanpa `model_path` valid → `weights_loaded == False` — **belum ada test formal, folder `tests/` belum dibuat (F8)**

**Catatan:** `model_status` ditambahkan ke `SimulationResponse` sebagai field `[EKSTENSI]`, ditandai di docstring skema. Keputusan TA.4 (2026-07-22) mengonfirmasi field ini diadopsi permanen dengan nama/bentuk seperti saat ini.

---

### TA.4 — Rekonsiliasi skema request/response

```
Status : DONE (parsial — lihat item #3)
Blokir : —
Dasar  : PRD §7.1 langkah 4 · Arsitektur §E.2, §E.3 · AGENTS.md §7.2
File   : app/models/schemas.py
Temuan : F6, F9
```

> **KEPUTUSAN KETUA TIM (2026-07-22):**
> 1. **Pertahankan** `compound_id`/`smiles_string` — TIDAK diganti ke `compound`/`smiles`.
> 2. **Adopsi** `model_status` (dari TA.3) sebagai field permanen.
> 3. Field `[EKSTENSI]` lain dari Arsitektur §E.3 (`engine`, `model_version`, `abstained`, `applicability_domain`) — **belum diputuskan**, tetap ditunda. Bukan blocker untuk task ini.

**Verifikasi keamanan keputusan #1 (audit ulang seluruh repo, 2026-07-22):** `grep -rn "compound_id\|smiles_string"` vs pencarian bentuk `compound`/`smiles` bare di seluruh `*.py` menunjukkan `compound_id`/`smiles_string` adalah SATU-SATUNYA penamaan yang dipakai di manapun di kode (schemas.py, simulation_orchestrator.py, errors.py, compounds.py, README.md) — nol referensi ke bentuk alternatif yang perlu dibereskan. Aman dipertahankan, tidak ada perubahan kode yang diperlukan untuk keputusan ini.

**Temuan sampingan (di luar cakupan task ini, dilaporkan bukan diperbaiki):** `openapi.json` di root repo isinya korup/bukan JSON valid (tampak seperti dump objek PowerShell yang salah encoding), independen dari keputusan TA.4 ini. Regenerasi butuh runtime Python/uvicorn yang tidak tersedia di sesi kerja ini — **belum dilakukan**, jangan diedit manual (instruksi task ini sendiri melarangnya).

**Selesai bila:**
- [x] Keputusan tim tercatat sebagai komentar di atas class `SimulationRequest`
- [x] Field `model_status` dari TA.3 sudah masuk skema
- [x] `README.md` contoh request/response sinkron dengan skema aktual
- [ ] `openapi.json` diregenerasi — **belum**, tidak ada runtime Python di environment ini

---

### TA.5 — Perbaiki exception handler agar tidak membocorkan detail internal

```
Status : DONE
Blokir : —
Dasar  : Arsitektur §E.4, §E.6 · AGENTS.md §6
File   : app/main.py
Temuan : F5
```

**Langkah:**
1. `global_exception_handler` saat ini mengembalikan `{"detail": "Internal Server Error", "error": str(exc)}` — hapus key `"error"` dari response ke client
2. Detail exception (`str(exc)`, traceback) tetap dicatat lewat `logging`, hanya tidak dikirim ke client
3. Tambahkan modul `app/core/errors.py` berisi kelas error spesifik minimal untuk kasus yang sudah muncul di kode saat ini: SMILES invalid (dipakai `simulation_orchestrator._simulate_triase` lewat `validate_smiles`), request tidak lengkap (`compound_id` kosong di mode edukasi)
4. Ganti `raise HTTPException(status_code=400, detail="...")` yang tersebar di `simulation_orchestrator.py` menjadi memakai kelas error baru ini, supaya kode error konsisten dan bisa diperluas nanti (lihat T0.3 di `EXECUTION_PLAN.md` untuk taksonomi lengkap yang menyusul)

**Selesai bila:**
- [ ] Memicu exception tak terduga → response client tidak memuat pesan exception mentah
- [ ] Log server tetap mencatat detail lengkap
- [ ] Endpoint `/simulate` dengan `smiles_string` invalid tetap mengembalikan error yang jelas ke client (perilaku tidak berubah, cuma sumber error-nya dirapikan)

---

### TA.6 — Cache dasar (opsional untuk audit ini, boleh ditunda)

```
Status : DONE (modul berdiri sendiri, belum diwiring ke /simulate)
Blokir : TA.4 (butuh model_version di skema untuk key cache)
Dasar  : Arsitektur §E.5
File   : app/core/cache.py (baru)
Temuan : —
```

**Catatan:** Task ini bukan perbaikan atas kesalahan yang ada, murni penambahan fitur yang memang sudah dijadwalkan `EXECUTION_PLAN.md` T0.4. Boleh dikerjakan setelah TA.1–TA.5 selesai, tidak mendesak untuk audit ini. Cukup dicatat di sini supaya urutannya jelas dan tidak dikerjakan mendahului perbaikan kritis.

**Diselesaikan 2026-07-22:** `app/core/cache.py` dibuat sesuai `EXECUTION_PLAN.md` T0.4 (tabel `cache(key, value, created_at)`, `make_key(engine, model_version, inchikey_block1, dose, duration)` via SHA-256, `get`/`set`/`clear`, tabel dibuat otomatis dari `settings.CACHE_DB_PATH`). **Blocker aslinya (`model_version` di skema) belum benar-benar dituntaskan** — TA.4 item #3 (apakah field `engine`/`model_version` diadopsi ke `SimulationResponse`) masih terbuka. Modul ini karena itu dibangun berdiri sendiri, TIDAK diwiring ke `simulation_orchestrator.py`/`/simulate`, karena belum ada nilai `model_version` nyata untuk dijadikan kunci. Wiring aktualnya dijadwalkan `EXECUTION_PLAN.md` T1.18 (Sprint 1), bukan sesi ini.

**Selesai bila (dari `EXECUTION_PLAN.md` T0.4, dipakai sebagai acuan karena TA.6 sendiri tidak punya checklist):**
- [x] `make_key()` menghasilkan kunci berbeda saat `model_version` berbeda, input lain identik (terverifikasi lewat pembacaan kode — `model_version` masuk komposisi string sebelum di-hash)
- [x] File DB dibuat otomatis di path dari config (`settings.CACHE_DB_PATH`, default `cache.db`)
- [ ] Test `set` lalu `get` mengembalikan nilai sama — **belum ada test formal**, folder `tests/` belum dibuat (F8)

---

### TA.7 — Endpoint daftar senyawa flagship

```
Status : DONE
Blokir : —
Dasar  : PRD §4.1 · Arsitektur §E.1
File   : app/api/endpoints/compounds.py (baru), app/api/router.py
Temuan : F7
```

**Langkah:**
1. `GET /api/v1/compounds` mengembalikan daftar 2 senyawa flagship sesuai PRD §4.1: `paracetamol` (hepatoselular dose-dependent) dan `amoxicillin_clavulanate` (kolestatik idiosinkratik)
2. Data cukup statis (list Python), tidak perlu database
3. Daftarkan router baru di `app/api/router.py`

**Selesai bila:**
- [x] Endpoint mengembalikan tepat 2 entri
- [x] Setiap entri memuat minimal: id, nama tampilan, tipe mekanisme

**Catatan:** id memakai `amox_clav` (bukan `amoxicillin_clavulanate` yang disebut teks task ini) supaya konsisten dengan nilai `compound_id` yang sudah ada di `SimulationRequest` (`app/models/schemas.py`) dan dipakai `simulation_orchestrator.py`. Ini bukan keputusan penamaan baru, hanya mengikuti nilai yang sudah berlaku di repo.

---

### TA.8 — Mode uji lokal tanpa gerbang (untuk development, bukan produksi)

```
Status : DONE
Blokir : TA.1
Dasar  : Arsitektur §H Sprint 0 hari 5 (mock mode)
File   : app/core/config.py, app/services/simulation_orchestrator.py
Temuan : —
```

**Konteks:** setelah TA.1 memasang `assert_ready()`, endpoint `/simulate` untuk parasetamol akan selalu gagal sampai konstanta PD tervalidasi Farmasi. Ini benar secara desain, tapi bisa memblokir kerja frontend yang cuma butuh bentuk response, bukan angka akurat.

**Langkah:**
1. Tambahkan `MOCK_MODE: bool = False` ke `Settings`
2. Bila `MOCK_MODE=True`, `simulation_orchestrator` mengembalikan response berbentuk final dengan nilai dummy yang **jelas ditandai dummy** (`model_status="mock"`, angka bulat mencolok seperti `0.5`)
3. Mode ini **tidak boleh aktif di deployment produksi** — beri komentar tegas di `.env.example`

**Selesai bila:**
- [x] `MOCK_MODE=True` → endpoint tetap merespons walau konstanta PD kosong
- [x] `MOCK_MODE=False` (default) → tetap terblokir `assert_ready()` sesuai TA.1
- [x] Response mock secara visual tidak mungkin disalahartikan sebagai hasil nyata (`model_status="mock"`, `DILI_score=0.5`, `compound_name="MOCK_COMPOUND"`, `explainability=["MOCK_MODE_ACTIVE"]`, disclaimer diberi prefix `[MOCK MODE]`)

**Catatan implementasi (2026-07-22):** `model_status` di `app/models/schemas.py` diperluas jadi `Literal["trained", "untrained_random_weights", "mock"]` — **perubahan skema, dilaporkan ke pengguna** karena menambah satu nilai enum baru yang perlu ditangani frontend. Validasi request dasar (`compound_id` valid, `smiles_string` ada & valid RDKit) tetap jalan sebelum masuk jalur mock — MOCK_MODE hanya melewati komputasi Mesin A/B, bukan validasi bentuk request.

---

### TA.9 — Perbarui AGENTS.md dengan larangan baru dari temuan F1

```
Status : DONE
Blokir : TA.3
Dasar  : Temuan audit ini sendiri
File   : AGENTS.md
Temuan : F1
```

**Langkah:**
Tambahkan larangan baru ke §3 `AGENTS.md`, penomoran lanjutan (§3.10):

> ### 3.10 JANGAN membiarkan model tanpa bobot terlatih berjalan tanpa penanda
>
> Bila artefak model (`model.pt` atau setara) tidak berhasil dimuat, sistem boleh tetap berjalan dengan bobot inisialisasi acak **hanya untuk keperluan development**, dan **wajib** menandainya secara eksplisit di response (`model_status` atau field setara). Dilarang mengembalikan skor dari model tak terlatih tanpa penanda ini, di lingkungan manapun.

**Selesai bila:**
- [x] `AGENTS.md` §3.10 ditambahkan
- [x] Bagian 11 (Status Proyek) di `AGENTS.md` diperbarui mencerminkan hasil audit ini

**Catatan:** repo ini tidak punya `AGENTS.md` terpisah di root — `docs/Claude.md` memuat isi lengkap kontrak perilaku (bukan pointer satu baris `@AGENTS.md` seperti disebut §4). §3.10 dan §11 diperbarui di `docs/Claude.md`.

---

## BAGIAN 3 — URUTAN EKSEKUSI YANG AMAN

Supaya tidak ada task yang saling tabrak file di commit yang sama:

```
1. TA.1  (pkpd_engine.py)                    — berdiri sendiri
2. TA.2  (ai_engine.py bagian SMARTS)         — berdiri sendiri, bisa paralel dengan TA.1
3. TA.3  (ai_engine.py bagian model status)   — sentuh file sama dengan TA.2, kerjakan SETELAH TA.2 selesai commit
4. TA.5  (main.py, errors.py baru)            — berdiri sendiri, bisa paralel dengan TA.1/TA.2
5. TA.7  (endpoint compounds baru)            — berdiri sendiri
6. TA.4  (schemas.py)                         — BLOCKED-HUMAN, tunggu keputusan tim, baru eksekusi
7. TA.8  (config.py + orchestrator)           — setelah TA.1 dan TA.4 selesai
8. TA.9  (AGENTS.md)                          — paling akhir, setelah TA.3 selesai
9. TA.6  (cache.py)                           — kapan saja setelah TA.4, tidak mendesak
```

**Aturan commit:** satu task = satu commit di branch `dev-vedo`. Jangan gabung beberapa task audit dalam satu commit — kalau ada yang perlu di-revert, harus bisa revert satu temuan tanpa membatalkan perbaikan lain.

---

## BAGIAN 4 — SETELAH AUDIT SELESAI

Checklist sebelum menganggap `dev-vedo` siap lanjut ke `EXECUTION_PLAN.md` Sprint 0 sisanya / Sprint 1:

- [ ] Semua item Bagian 1 (F1–F9) berstatus selesai atau `BLOCKED-HUMAN` dengan alasan jelas — **F8 (folder `tests/` belum ada) masih terbuka, belum ada task yang menuntaskannya**
- [x] `grep -rn "K_IN = 1\|K_GSH = 2\|THETA_THRESHOLD = 0" app/` → nol hasil
- [x] `grep -rn "0.1 \* t" app/services/pkpd_engine.py` → nol hasil
- [x] Server menyala dengan `MOCK_MODE=False` dan gagal jelas (bukan diam-diam salah) saat konstanta PD kosong (TA.8 selesai)
- [x] `README.md` diperbarui mencerminkan `model_status` dan keputusan skema dari TA.4
- [x] `AGENTS.md` §3.10 dan Bagian 11 sudah diperbarui (di `docs/Claude.md`)
- [ ] Status task terkait di `EXECUTION_PLAN.md` (T0.2, T0.3, T0.4, T0.6, T0.7) disesuaikan — **belum dikerjakan**, di luar cakupan sesi ini

**Setelah checklist ini lulus, lanjutkan ke `EXECUTION_PLAN.md` mulai T0.8 (bila belum terkirim) dan Sprint 1.**
