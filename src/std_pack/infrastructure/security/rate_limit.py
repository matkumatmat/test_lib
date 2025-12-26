"""
Rate Limiting Module.
Membatasi jumlah request menggunakan Redis (Fixed Window Algorithm).
"""
from typing import Annotated

from fastapi import Depends, Request
from redis import asyncio as aioredis

from std_pack.infrastructure.security.scheme import get_current_user, IAuthUser
from std_pack.domain.exceptions import TooManyRequestsError

class RateLimiter:
    """
    Dependency untuk membatasi request.
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
        # Mengambil Redis dari request.state (nanti di-inject via Middleware di Main App)
        redis: aioredis.Redis = getattr(request.state, "redis", None)
        
        if not redis:
            # Jika Redis belum disetup di App, skip rate limit (Fail Open)
            return

        # 1. Tentukan Identity (User ID jika login, atau IP Address)
        identity = str(user.id) if user else (request.client.host if request.client else "unknown")
        
        # 2. Key: rl:{identity}:{path}:{method}
        key = f"rl:{identity}:{request.url.path}:{request.method}"
        
        # 3. Eksekusi Redis (Atomic)
        pipe = redis.pipeline()
        pipe.incr(key, 1)
        pipe.ttl(key)
        result = await pipe.execute()
        
        request_count = result[0]
        ttl = result[1]
        
        # 4. Set Expire jika key baru
        if request_count == 1:
            await redis.expire(key, self.seconds)
            ttl = self.seconds
        
        # 5. Cek Limit
        if request_count > self.times:
            retry_after = ttl if ttl > 0 else self.seconds
            raise TooManyRequestsError(retry_after=retry_after)