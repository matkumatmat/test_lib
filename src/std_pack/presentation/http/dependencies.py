"""
HTTP Dependencies.
Reusable dependencies untuk Route (Auth, Rate Limit, dll).
"""
from typing import Annotated, Protocol

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from redis import asyncio as aioredis

from std_pack.config import BaseAppSettings
from std_pack.domain.exceptions import UnauthorizedError, TooManyRequestsError
from std_pack.infrastructure.security.token import TokenHelper

# --- AUTH DEPENDENCIES ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None

def get_current_token_payload(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """Validasi Token JWT dari Header."""
    settings = BaseAppSettings() 
    helper = TokenHelper(settings)
    
    try:
        payload = helper.decode_token(token)
        return payload
    except Exception as e:
        raise UnauthorizedError(f"Could not validate credentials: {str(e)}")

class IAuthUser(Protocol):
    """Kontrak User Object."""
    id: int | str
    roles: list[str]
    is_active: bool

async def get_current_user(
    payload: Annotated[dict, Depends(get_current_token_payload)]
) -> IAuthUser:
    """
    Dependency Abstrak. Wajib di-override di App User.
    app.dependency_overrides[get_current_user] = get_real_user
    """
    raise NotImplementedError("Dependency 'get_current_user' must be overridden in main app!")


# --- RATE LIMIT DEPENDENCIES ---

class RateLimiter:
    """
    Dependency untuk membatasi request (Throttling).
    Penggunaan: Depends(RateLimiter(times=10, seconds=60))
    """
    def __init__(self, times: int = 10, seconds: int = 60):
        self.times = times
        self.seconds = seconds

    async def __call__(
        self, 
        request: Request,
        user: Annotated[IAuthUser, Depends(get_current_user)],
    ):
        # Ambil Redis dari app.state (yang diset oleh Bootstrap)
        redis: aioredis.Redis = getattr(request.state, "redis", None)
        
        if not redis:
            return # Fail open jika Redis mati/tidak ada

        identity = str(user.id) if user else (request.client.host if request.client else "unknown")
        key = f"rl:{identity}:{request.url.path}:{request.method}"
        
        # Atomic Increment & TTL
        pipe = redis.pipeline()
        pipe.incr(key, 1)
        pipe.ttl(key)
        result = await pipe.execute()
        
        request_count = result[0]
        ttl = result[1]
        
        if request_count == 1:
            await redis.expire(key, self.seconds)
            ttl = self.seconds
        
        if request_count > self.times:
            retry_after = ttl if ttl > 0 else self.seconds
            raise TooManyRequestsError(retry_after=retry_after)