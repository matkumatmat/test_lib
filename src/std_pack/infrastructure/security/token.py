"""
Security Token Module.
Menangani pembuatan dan verifikasi JWT (JSON Web Token).
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from std_pack.config import BaseAppSettings

class TokenHelper:
    def __init__(self, settings: BaseAppSettings):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256" # Default algorithm yang aman dan cepat

    def create_access_token(
        self, 
        subject: str | Any, 
        expires_delta: timedelta | None = None
    ) -> str:
        """
        Membuat JWT Access Token.
        :param subject: Identitas utama (misal: User ID atau Email).
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Default durasi token: 30 menit
            expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        # Claims standar JWT (exp, sub, iat)
        to_encode = {
            "exp": expire, 
            "sub": str(subject),
            "iat": datetime.now(timezone.utc)
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt

    def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decode token dan verifikasi signature.
        Raise ValueError jika token invalid atau expired.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            # Re-raise sebagai ValueError agar pesan error bersih
            raise ValueError(str(e))