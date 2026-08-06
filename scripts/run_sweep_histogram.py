"""Freeze the PRD v2.3 PBPK exposure calibration from a read-only catalog snapshot."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.models.domain import HepatwinCompound
from app.services import pbpk_calibration
from app.services.pbpk_engine import PBPKEngine

AGES = (0, 15, 16, 40, 90, 100)
BMIS = tuple(range(16, 41, 2))
DOSES_MG_KG = (0.5, 2, 5, 10, 15, 20, 30, 40, 50)
HEIGHT_CM_BY_GENDER = {"L": 170.0, "P": 160.0}
CALIBRATION_VERSION = "PBPK_EXPOSURE_CALIBRATION_V2_3"


def _normalise_xlogp(value: float | None) -> float:
    if value is None or not np.isfinite(float(value)):
        return 0.0
    return float(value)


def load_catalog_snapshot() -> tuple[list[dict[str, Any]], str]:
    db = SessionLocal()
    try:
        rows = db.execute(
            select(HepatwinCompound.hepatwin_id, HepatwinCompound.xlogp)
            .where(HepatwinCompound.is_simulatable.is_(True))
            .order_by(HepatwinCompound.hepatwin_id)
        ).all()
    finally:
        db.close()
    snapshot = [
        {"hepatwin_id": str(row.hepatwin_id), "xlogp": _normalise_xlogp(row.xlogp)}
        for row in rows
    ]
    if not snapshot:
        raise RuntimeError("Snapshot katalog simulatable kosong; calibration dihentikan.")
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return snapshot, hashlib.sha256(payload).hexdigest()


def _write_runtime_calibration(
    path: Path, p33: float, p66: float, snapshot_hash: str, config_hash: str, timestamp: str
) -> None:
    source = path.read_text(encoding="utf-8")
    replacements = {
        "CALIBRATION_VERSION": repr(CALIBRATION_VERSION),
        "CATALOG_SNAPSHOT_SHA256": repr(snapshot_hash),
        "CATALOG_SNAPSHOT_TIMESTAMP_UTC": repr(timestamp),
        "PBPK_CONFIG_SHA256": repr(config_hash),
        "P33_EXPOSURE_INDEX": repr(p33),
        "P66_EXPOSURE_INDEX": repr(p66),
    }
    for name, value in replacements.items():
        source, replacements_made = re.subn(
            rf"^{name} = .*$", f"{name} = {value}", source, count=1, flags=re.MULTILINE
        )
        if replacements_made != 1:
            raise RuntimeError(f"Runtime calibration constant '{name}' tidak ditemukan.")
    path.write_text(source, encoding="utf-8")


def _run_demographic_sweep(task: tuple[int, str, float, float, tuple[tuple[float, int], ...]]) -> list[tuple[float, int]]:
    logging.getLogger("app.services.allometric_service").setLevel(logging.ERROR)
    age, gender, height_cm, bmi, xlogp_counts = task
    weight_kg = bmi * (height_cm / 100.0) ** 2
    engine = PBPKEngine()
    results: list[tuple[float, int]] = []
    for xlogp, catalog_count in xlogp_counts:
        base = engine.simulate_with_diagnostics(1.0, age, gender, weight_kg, height_cm, xlogp=xlogp)
        for dose_mg_kg in DOSES_MG_KG:
            dose_mg = dose_mg_kg * weight_kg
            cmax = base.cmax_hati * dose_mg
            auc = base.auc_hati * dose_mg
            results.append((float(np.log1p(cmax) + np.log1p(auc)), catalog_count))
    return results


def run_sweep() -> dict[str, Any]:
    snapshot, snapshot_hash = load_catalog_snapshot()
    config_snapshot = pbpk_calibration.runtime_pbpk_config_snapshot()
    config_hash = pbpk_calibration.runtime_pbpk_config_sha256()
    xlogp_counts = Counter(row["xlogp"] for row in snapshot)
    exposure_indices: list[float] = []
    frozen_xlogp_counts = tuple(sorted(xlogp_counts.items()))
    tasks = [
        (age, gender, height_cm, bmi, frozen_xlogp_counts)
        for age in AGES
        for gender, height_cm in HEIGHT_CM_BY_GENDER.items()
        for bmi in BMIS
    ]
    worker_count = min(os.cpu_count() or 1, len(tasks))
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        for demographic_results in executor.map(_run_demographic_sweep, tasks):
            for exposure_index, catalog_count in demographic_results:
                exposure_indices.extend([exposure_index] * catalog_count)

    values = np.asarray(exposure_indices, dtype=float)
    p33, p66 = (float(np.quantile(values, q)) for q in (0.33, 0.66))
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    categories = {
        "LOW_EXPOSURE": int(np.sum(values < p33)),
        "MODERATE_EXPOSURE": int(np.sum((values >= p33) & (values <= p66))),
        "HIGH_EXPOSURE": int(np.sum(values > p66)),
    }
    report = {
        "version": CALIBRATION_VERSION,
        "source": "INTERNAL_DISTRIBUTIONAL_CALIBRATION",
        "timestamp_utc": timestamp,
        "catalog_snapshot_sha256": snapshot_hash,
        "pbpk_config_sha256": config_hash,
        "pbpk_config": config_snapshot,
        "catalog_rows": len(snapshot),
        "xlogp_values": len(xlogp_counts),
        "grid": {
            "ages": AGES,
            "bmis": BMIS,
            "height_cm_by_gender": HEIGHT_CM_BY_GENDER,
            "doses_mg_kg": DOSES_MG_KG,
        },
        "samples": int(values.size),
        "p33_exposure_index": p33,
        "p66_exposure_index": p66,
        "category_counts": categories,
    }
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    (reports_dir / "pbpk_exposure_calibration_v2_3.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (reports_dir / "pbpk_exposure_calibration_v2_3.md").write_text(
        "\n".join(
            [
                "# PBPK Exposure Calibration v2.3",
                "",
                "Internal distributional calibration; not a clinical threshold.",
                "",
                f"- Snapshot SHA-256: `{snapshot_hash}`",
                f"- PBPK config SHA-256: `{config_hash}`",
                f"- Timestamp UTC: `{timestamp}`",
                f"- Catalog rows: {len(snapshot)}; distinct effective XLogP: {len(xlogp_counts)}",
                f"- Samples: {values.size}",
                f"- P33 exposure_index: {p33:.12g}",
                f"- P66 exposure_index: {p66:.12g}",
                f"- Category counts: {categories}",
                f"- Grid: age={AGES}; BMI={BMIS}; dose mg/kg={DOSES_MG_KG}; heights={HEIGHT_CM_BY_GENDER}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_runtime_calibration(
        Path("app/services/pbpk_calibration.py"), p33, p66, snapshot_hash, config_hash, timestamp
    )
    return report


if __name__ == "__main__":
    result = run_sweep()
    print(json.dumps(result, indent=2, ensure_ascii=False))
