# F4 -- Intensitas & Mode Hotspot (Gap PRD SS3.3)

## 1. Field baru diteruskan ke `SimulationResponse`

`hotspot_intensity`, `hotspot_display_mode`, `evidence_note` -- diambil dari kolom DB
`hotspot_base_intensity`/`hotspot_display_mode` yang sudah ada di skema (`app/models/domain.py`)
tapi tidak pernah dibaca orchestrator (PROJECT_FUSION.md SS3.3).

Verifikasi lewat query langsung ke seluruh 1.231 senyawa `is_simulatable=TRUE`, pemetaan `injury_pattern`
-> `(hotspot_base_intensity, hotspot_display_mode)` persis sesuai tabel PROJECT_FUSION.md SS4.3:

| injury_pattern | hotspot_base_intensity | hotspot_display_mode | n |
|---|---|---|---|
| Hepatoseluler | high | focal | 236 |
| Kolestatik | high | focal | 128 |
| Campuran | low | diffuse | 43 |
| Tidak Terklasifikasi | dim | diffuse | 824 |

`evidence_note` diisi HANYA bila `injury_pattern == "Tidak Terklasifikasi"` atau `segment_list` kosong,
dengan kalimat netral (tidak mengklaim "terbukti tidak ada cedera") sesuai gerbang K6 (default: tidak
menambah kolom skema DB baru).

## 2. \U0001F6A9 TEMUAN BARU: bug pemisah `affected_segments` (di luar SS3.1-3.5)

Ditemukan saat memverifikasi field ini: `segment_list` di database NYATA memakai pemisah **titik-koma**
(`;`), bukan koma -- diverifikasi lewat query pada seluruh 1.231 senyawa, konsisten di keempat kategori
`injury_pattern` (mis. `"V;VI;VII;VIII"`). Kode lama di `simulation_orchestrator.py`
(`compound.segment_list.split(",")`) mengasumsikan koma. Karena TIDAK ADA satu pun baris data nyata yang
memakai koma, `split(",")` **tidak pernah benar-benar memecah apa pun** -- `affected_segments` yang
dikirim ke frontend selalu berisi **satu string gabungan yang salah** (mis. `["V;VI;VII;VIII"]`), untuk
**100% dari 1.231 senyawa**, sejak kode ini pertama ada di `master`.

Bug ini tidak pernah tertangkap oleh test suite karena satu-satunya assertion terkait
(`tests/unit/test_api.py`) memakai data mock buatan sendiri dengan koma (`"V, VI, VII, VIII"`), bukan
data asli, dan hanya memeriksa keberadaan key (`"affected_segments" in res_data`), bukan isinya.

**Diperbaiki di sini** (`app/services/simulation_orchestrator.py`, ganti `split(",")` -> `split(";")`),
karena letaknya persis di kode yang sama yang disentuh F4 (lookup segmen), dan efeknya langsung
memengaruhi apakah frontend bisa menyorot segmen Couinaud yang benar (UC-03) -- bagian inti dari D9.

Fixture test juga diperbarui supaya konsisten dengan format data nyata:
- `tests/conftest.py` (22 baris `segment_list`, dipakai seluruh e2e test suite)
- `tests/e2e/test_b7_lookup_e2e.py` (20 baris nilai `expected["segment_list"]`)
- `tests/unit/test_api.py` (1 mock)

## 3. Verifikasi manual (smoke test end-to-end, bukan lewat HTTP mock)

- **HT0012 (Acetaminophen, Hepatoseluler), dosis 4000mg/70kg/40th:**
  `affected_segments=['V','VI','VII','VIII']` (sebelumnya: `['V;VI;VII;VIII']` -- satu elemen salah),
  `hotspot_intensity=high`, `hotspot_display_mode=focal`, `evidence_note=None`.
- **HT0178 (Calcitonin salmon, vNo, Tidak Terklasifikasi), dosis 200mg/65kg/30th:**
  `affected_segments` = 8 segmen penuh, `hotspot_intensity=dim`, `hotspot_display_mode=diffuse`,
  `evidence_note` terisi kalimat netral fallback.
- Intensitas terbukti **tidak** memengaruhi warna: `visual_color`/`risk_level`/`blinking_speed` murni
  dari `FusionResult` (F3), field hotspot murni dari lookup DB terpisah -- dua kompaound di atas
  membuktikan jalur independen (HT0012 merah+focal/high, HT0178 merah [krn HIGH_EXPOSURE, temuan F2]
  +diffuse/dim -- warna sama-sama merah dengan intensitas berbeda pada kasus ini karena kebetulan
  exposure_category-nya sama, tapi mekanismenya tetap independen; pembuktian formal 2 senyawa skor sama
  x intensitas beda -> warna sama akan diformalkan sebagai test di F8).

## 4. Pytest

143 passed setelah perubahan (baseline F0: 143), tidak ada regresi.
