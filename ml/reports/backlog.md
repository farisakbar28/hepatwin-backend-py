# backlog.md — Temuan di luar cakupan C1–C12 (Alur Kerja C)

Catatan sesuai `EXECUTION_PLAN_FIX_MODEL.md` Aturan Main #7 ("Jangan melebarkan
cakupan") — temuan yang muncul selama pengerjaan C1–C12 tapi bukan tanggung
jawab Alur C dicatat di sini, bukan diperbaiki langsung.

## 1. `segment_list` delimiter mismatch di `simulation_orchestrator.py`

**Ditemukan saat:** C2 (loader Supabase), lewat inspeksi data nyata.

**Fakta:** kolom `segment_list` di `hepatwin_compounds` berisi nilai yang
dipisah **titik koma**, mis. `"V;VI;VII;VIII"` (diverifikasi lewat query
langsung ke Supabase). Tapi `app/services/simulation_orchestrator.py` baris
92 melakukan:

```python
affected_segments = [s.strip() for s in compound.segment_list.split(",") if s.strip()]
```

— split pada **koma**, bukan titik koma. Untuk nilai `"V;VI;VII;VIII"`, ini
menghasilkan list satu elemen `["V;VI;VII;VIII"]`, bukan 4 elemen
`["V","VI","VII","VIII"]` seperti yang dimaksud.

**Dampak:** `SimulationResponse.affected_segments` (dikonsumsi frontend Alur E
untuk highlight segmen Couinaud 3D) kemungkinan salah untuk semua senyawa yang
py punya >1 segmen di `segment_list`.

**Kenapa tidak diperbaiki di sini:** `simulation_orchestrator.py` adalah milik
Alur F (fusi), PIC Faris — eksplisit di luar cakupan `PROJECT_FIX_MODEL.md` §6
("Mengubah logika autocomplete / `compound_repository.py` / `lookup_service.py`").
Meski file yang bug bukan persis salah satu dari ketiga nama itu, ia bagian
dari lapisan runtime yang sama (§5.1: "sudah benar untuk zona" — temuan ini
menunjukkan itu tidak sepenuhnya akurat untuk field `segment_list`).

**Rekomendasi:** ganti `.split(",")` → `.split(";")` di
`simulation_orchestrator.py` baris 92. Perbaikan satu baris, tidak menyentuh
logika lain.
