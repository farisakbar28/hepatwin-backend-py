"""Taksonomi error HepaTwin (audit TA.5).

Ini himpunan minimal untuk kasus yang sudah muncul di kode saat ini.
Taksonomi lengkap sesuai Arsitektur §E.4 dijadwalkan di EXECUTION_PLAN.md T0.3
(E_SMILES_INVALID, E_MOL_TOO_LARGE, E_INORGANIC, E_MIXTURE, E_DOSE_RANGE,
E_MODEL_UNAVAILABLE) dan akan menggantikan/melengkapi modul ini.
"""


class HepaTwinError(Exception):
    """Base class error HepaTwin. Turunkan untuk setiap kondisi error spesifik."""

    code: str = "E_UNKNOWN"
    http_status: int = 400

    def __init__(self, user_message: str):
        self.user_message = user_message
        super().__init__(user_message)


class SmilesInvalidError(HepaTwinError):
    """RDKit gagal memparse SMILES. Dasar: Arsitektur §E.4."""

    code = "E_SMILES_INVALID"
    http_status = 422

    def __init__(self, user_message: str = "Notasi SMILES tidak dapat dibaca"):
        super().__init__(user_message)


class RequestIncompleteError(HepaTwinError):
    """Field wajib untuk mode yang dipilih tidak diisi
    (mis. compound_id kosong pada mode edukasi_mendalam, atau
    smiles_string kosong pada mode triase_umum)."""

    code = "E_REQUEST_INCOMPLETE"
    http_status = 422

    def __init__(self, user_message: str):
        super().__init__(user_message)
