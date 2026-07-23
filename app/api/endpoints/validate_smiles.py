from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.chem.standardize import check_eligibility, standardize
from app.core.errors import (
    InorganicError,
    MixtureError,
    MolTooLargeError,
)

router = APIRouter()


class ValidateSmilesRequest(BaseModel):
    smiles: str = Field(..., min_length=1, max_length=500)


class ValidateSmilesResponse(BaseModel):
    valid: bool
    error_code: str | None = None
    canonical_smiles: str | None = None


@router.post("/validate-smiles", response_model=ValidateSmilesResponse)
def validate_smiles(request: ValidateSmilesRequest):
    """
    Validasi SMILES untuk frontend (PRD §7.1 langkah 1).

    Endpoint ini ringan dan cepat — tidak memuat model ML, hanya RDKit.
    Dipanggil saat pengguna mengetik di Mode Triase Umum.
    """
    smiles = request.smiles.strip()

    if not smiles:
        return ValidateSmilesResponse(valid=False, error_code="E_SMILES_INVALID")

    try:
        std = standardize(smiles)
        if std is None:
            return ValidateSmilesResponse(valid=False, error_code="E_SMILES_INVALID")

        # Cek kelayakan (atom count, organik, campuran)
        try:
            check_eligibility(std)
        except MolTooLargeError as e:
            return ValidateSmilesResponse(valid=False, error_code=e.code)
        except InorganicError as e:
            return ValidateSmilesResponse(valid=False, error_code=e.code)
        except MixtureError as e:
            return ValidateSmilesResponse(valid=False, error_code=e.code)

        return ValidateSmilesResponse(
            valid=True,
            canonical_smiles=std.canonical_smiles,
        )
    except MolTooLargeError as e:
        return ValidateSmilesResponse(valid=False, error_code=e.code)
    except InorganicError as e:
        return ValidateSmilesResponse(valid=False, error_code=e.code)
    except MixtureError as e:
        return ValidateSmilesResponse(valid=False, error_code=e.code)
    except Exception:
        return ValidateSmilesResponse(valid=False, error_code="E_SMILES_INVALID")
