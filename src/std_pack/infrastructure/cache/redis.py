"""
Redis Cache Wrapper.
Menangani koneksi ke Redis untuk Caching, Rate Limiting, dan Pub/Sub.
"""
from typing import Optional

# Pastikan user sudah install: poetry add redis
from redis import asyncio as aioredis
from std_pack.infrastructure.logging import get_logger

logger = get_logger(__name__)

class RedisManager:
    """
    Manajer koneksi Redis.
    Bersifat 'Lazy': Koneksi baru dibuat saat init_cache dipanggil.
    """
    def __init__(self, url: str):
        self.url = url
        self.client: Optional[aioredis.Redis] = None

    async def init_cache(self) -> None:
        """Inisialisasi koneksi Redis."""
        # Masking URL untuk log (jika ada password)
        masked_url = self.url.split("@")[-1] if "@" in self.url else self.url
        logger.info("redis_initializing", url=masked_url)
        
        try:
            # from_url otomatis mengelola connection pool
            self.client = aioredis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True, # Penting: agar return string, bukan bytes
                socket_timeout=5.0,
                health_check_interval=30
            )
            
            # Test Ping untuk memastikan koneksi hidup
            await self.client.ping()
            logger.info("redis_connected_success")
            
        except Exception as e:
            logger.critical("redis_connection_failed", error=str(e))
            # Kita raise error agar aplikasi sadar kalau cache mati (bisa fatal buat Rate Limit)
            raise e

    async def close(self) -> None:
        """Tutup koneksi dengan bersih."""
        if self.client:
            await self.client.aclose() # type: ignore
            logger.info("redis_connection_closed")

    def get_client(self) -> aioredis.Redis:
        """
        Getter untuk mengambil client Redis raw.
        Akan error jika init_cache belum dipanggil.
        """
        if not self.client:
            raise RuntimeError(
                "Redis client belum siap! "
                "Pastikan Anda memanggil 'await redis_manager.init_cache()' saat startup."
            )
        return self.client