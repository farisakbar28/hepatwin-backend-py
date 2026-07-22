"""Taksonomi error HepaTwin (audit TA.5, dilengkapi EXECUTION_PLAN.md T0.3).

Taksonomi mengikuti Arsitektur §E.4. Setiap error membawa `code` (dipakai
frontend untuk memetakan pesan UI) dan `http_status`. Handler di `app/main.py`
mengubahnya jadi JSON `{code, detail}` tanpa stack trace.
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


class MolTooLargeError(HepaTwinError):
    """Jumlah atom berat di luar rentang model (<5 atau >100). Arsitektur §E.4."""

    code = "E_MOL_TOO_LARGE"
    http_status = 422

    def __init__(self, user_message: str = "Molekul di luar cakupan model"):
        super().__init__(user_message)


class InorganicError(HepaTwinError):
    """Mengandung atom di luar himpunan organik yang didukung. Arsitektur §E.4."""

    code = "E_INORGANIC"
    http_status = 422

    def __init__(self, user_message: str = "Senyawa anorganik/logam tidak didukung"):
        super().__init__(user_message)


class MixtureError(HepaTwinError):
    """Masih berupa campuran (mengandung '.') setelah standardisasi. Arsitektur §E.4."""

    code = "E_MIXTURE"
    http_status = 422

    def __init__(self, user_message: str = "Masukkan satu senyawa tunggal"):
        super().__init__(user_message)


class DoseRangeError(HepaTwinError):
    """Dosis di luar batas simulasi. Arsitektur §E.4."""

    code = "E_DOSE_RANGE"
    http_status = 422

    def __init__(self, user_message: str = "Dosis di luar rentang simulasi"):
        super().__init__(user_message)


class ModelUnavailableError(HepaTwinError):
    """Artefak model gagal dimuat. Arsitektur §E.4."""

    code = "E_MODEL_UNAVAILABLE"
    http_status = 503

    def __init__(self, user_message: str = "Layanan model sedang tidak tersedia"):
        super().__init__(user_message)


class RequestIncompleteError(HepaTwinError):
    """Field wajib untuk mode yang dipilih tidak diisi
    (mis. compound_id kosong pada mode edukasi_mendalam, atau
    smiles_string kosong pada mode triase_umum)."""

    code = "E_REQUEST_INCOMPLETE"
    http_status = 422

    def __init__(self, user_message: str):
        super().__init__(user_message)
