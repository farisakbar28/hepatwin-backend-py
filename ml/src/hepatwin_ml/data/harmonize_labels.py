"""TU.3 -- Harmonisasi label DILIrank (vDILI-Concern -> label_binary).

[KEPUTUSAN AI -- PENDING REVIEW FARMASI]: skema binerisasi (vMost+vLess=1,
vNo=0, Ambiguous dibuang) mengikuti default yang sudah tertulis di
UPSCALE.md SS3.2 sejak v1.0 dan konsisten dengan literatur DILI-ML rujukan
(Yang et al. 2024, Wibowo et al. 2025). Lihat EXECUTION_PLAN_UPSCALE.md
SS14.1 gerbang B2 -- keputusan ini bersifat sementara, wajib dikonfirmasi
Farmasi sebelum dianggap final (Definition of Done SS11 UPSCALE.md).

Perbandingan case-insensitive: file sumber DILIrank 2.0 punya varian
kapitalisasi tidak konsisten pada kolom vDILI-Concern (mis. "vMost-DILI-concern"
vs "vMOST-DILI-concern" vs "vNo-DILI-Concern") -- diverifikasi langsung di
ml/reports/01_dilirank_inspection.md.
"""
from typing import Optional

_POSITIVE = {"vmost-dili-concern", "vless-dili-concern"}
_NEGATIVE = {"vno-dili-concern"}
_DROPPED = {"ambiguous-dili-concern"}


def harmonize_vdili_concern(raw: str) -> Optional[int]:
    """vDILI-Concern (varian kapitalisasi apa pun) -> 1/0/None (None = dibuang)."""
    if not raw or not isinstance(raw, str):
        return None
    key = raw.strip().lower()
    if key in _POSITIVE:
        return 1
    if key in _NEGATIVE:
        return 0
    if key in _DROPPED:
        return None
    raise ValueError(f"Nilai vDILI-Concern tak dikenal: {raw!r}")
