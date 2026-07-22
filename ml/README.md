# ml/ — Pipeline Data & Training (TIDAK masuk Docker image)

Folder ini berisi seluruh kode training, kurasi data, dan evaluasi. Dijalankan
terpisah dari runtime API (`app/`). Aturan AGENTS.md §4: `ml/` boleh mengimpor
dari `app/`, sebaliknya **dilarang**.

## Struktur

```
ml/
├── data/           # gitignored — dataset mentah/olahan tidak masuk git
│   ├── raw/        # DILIrank (FDA LTKB), Xu et al. 2015 — apa adanya dari sumber
│   ├── interim/    # hasil antara (resolusi SMILES, standardisasi)
│   └── processed/  # train/valid/external_test final
├── scripts/        # 01_download → 07_external_eval (jalankan berurutan)
├── reports/        # ringkasan tiap tahap (baris masuk/keluar, metrik, plot)
└── notebooks/      # eksplorasi
```

## Urutan eksekusi (EXECUTION_PLAN.md Sprint 1)

```
01_download.py        # unduh DILIrank + Xu et al., catat lisensi ke NOTICE.md
02_resolve_smiles.py  # nama obat DILIrank → SMILES (PubChem, cache ke disk)
03_standardize.py     # RDKit standardize, map label biner, filter kelayakan
04_dedup_split.py     # dedup InChIKey blok-1 (BUKAN SMILES string), scaffold split
05_train_baseline.py  # LightGBM 5-fold CV → angka nyata pertama
06a_train_gnn.py      # GNN (gerbang kelayakan D.5)
06_train_production.py # latih model final di jalur terpilih
07_external_eval.py   # SATU KALI — buka external test, AGENTS.md §3.4
```

## Prinsip integritas (AGENTS.md §3, §10)

- Featurizer WAJIB diimpor dari `app/chem/features.py` — jangan disalin.
- External test (Xu et al.) hanya dibuka **sekali** di `07`, tidak untuk cek cepat.
- Dedup pakai **blok pertama InChIKey (14 karakter)**, bukan SMILES kanonik.
- Angka performa hanya dari eksekusi nyata; tidak ada yang boleh dikarang.
