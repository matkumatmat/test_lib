"""
Security Scheme & Dependencies.
Mengintegrasikan FastAPI Security dengan Logic Auth Library.
Menggunakan Custom Exception agar output error konsisten.
"""
from typing import Annotated, Protocol

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# Import Helper Token & Exception Domain
from .token import TokenHelper
from std_pack.config import BaseAppSettings
from std_pack.domain.exceptions import UnauthorizedError

# Setup OAuth2 Scheme (Agar muncul tombol 'Authorize' di Swagger)
# tokenUrl ini mengarah ke endpoint login di API Anda
# Pastikan nanti di App Anda membuat endpoint: POST /api/v1/auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class TokenPayload(BaseModel):
    """Schema payload token standar."""
    sub: str | None = None
    exp: int | None = None


# Dependency: Get Token Payload
def get_current_token_payload(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """
    Validasi Token JWT. 
    Jika gagal, raise UnauthorizedError (bukan HTTPException).
    """
    # Load Settings & Helper
    # Di aplikasi nyata, settings bisa di-inject via Dependency Override jika perlu
    settings = BaseAppSettings() 
    helper = TokenHelper(settings)
    
    try:
        # Decode & Verify Signature
        payload = helper.decode_token(token)
        return payload
    except Exception as e:
        # PENTING: Raise Domain Exception.
        # Handler global akan mengubahnya jadi HTTP 401 dengan format JSON standar library.
        raise UnauthorizedError(f"Could not validate credentials: {str(e)}")


# Protocol untuk User Service (Abstraction)
class IAuthUser(Protocol):
    """
    Kontrak User Object yang diharapkan oleh Security Layer.
    Objek User di App Anda harus memiliki atribut/method ini.
    """
    id: int | str
    roles: list[str]
    is_active: bool


# Dependency placeholder (Di-override di App nanti)
async def get_current_user(
    payload: Annotated[dict, Depends(get_current_token_payload)]
) -> IAuthUser:
    """
    Dependency Abstrak untuk mendapatkan User dari DB berdasarkan Token.
    
    Wajib di-override di main.py aplikasi Anda:
    app.dependency_overrides[get_current_user] = get_real_user_from_db
    """
    raise NotImplementedError(
        "Dependency 'get_current_user' belum di-implementasi! "
        "Harap override dependency ini di level Aplikasi."
    )