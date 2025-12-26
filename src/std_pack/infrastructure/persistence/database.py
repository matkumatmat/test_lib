# src/std_pack/infrastructure/persistence/database.py

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from std_pack.infrastructure.logging import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """
    Mengelola koneksi fisik ke Database.
    Choosable: User "memilih" database hanya dengan mengganti string URL.
    """
    
    def __init__(self, url: str, echo: bool = False):
        self.url = url
        self.echo = echo
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    def init_db(self) -> None:
        """Create Engine sesuai URL (Postgres/SQLite)."""
        logger.info("db_initializing", url=self._mask_url(self.url))
        
        # Konfigurasi argumen engine agar support multi-db
        connect_args = {}
        if "sqlite" in self.url:
            # SQLite butuh ini agar tidak error saat multithreading
            connect_args = {"check_same_thread": False}
        
        try:
            self.engine = create_async_engine(
                self.url,
                echo=self.echo,
                connect_args=connect_args,
                pool_pre_ping=True # Auto-reconnect jika putus
            )
            
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False, # Penting untuk Async
                autoflush=False
            )
            logger.info("db_connected_success")
            
        except Exception as e:
            logger.critical("db_connection_failed", error=str(e))
            raise e

    async def close(self) -> None:
        """Tutup koneksi."""
        if self.engine:
            await self.engine.dispose()
            logger.info("db_connection_closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Menyediakan sesi untuk Unit of Work."""
        if not self.session_factory:
            raise RuntimeError("DB belum di-init!")
            
        async with self.session_factory() as session:
            yield session

    def _mask_url(self, url: str) -> str:
        """Sensor password di log."""
        if "@" in url:
            part = url.split("@")
            return f"***@{part[1]}"
        return "local_db"