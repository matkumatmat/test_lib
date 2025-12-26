"""
Unit of Work Implementation.
Menangani transaksi database menggunakan SQLAlchemy Session.
Menghubungkan Application Layer (IUnitOfWork) dengan Infrastructure (Database).
"""
from typing import Type, Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from std_pack.application.interfaces.ports import IUnitOfWork


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """
    Implementasi Unit of Work untuk SQLAlchemy.
    
    Cara kerja:
    1. Saat `async with uow:` -> Buka session baru.
    2. Saat `uow.commit()` -> Simpan permanen ke DB.
    3. Saat keluar blok (exit) -> Tutup session (auto rollback jika error).
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        """Mulai transaksi baru (Start Transaction)."""
        self.session = self.session_factory()
        return self

    async def __aexit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, traceback: Any) -> None:
        """Selesai transaksi (End Transaction)."""
        if self.session:
            if exc_type:
                # Jika terjadi error di dalam blok 'async with', rollback otomatis
                await self.rollback()
            
            # Tutup session agar koneksi kembali ke pool
            await self.session.close()

    async def commit(self) -> None:
        """Commit transaksi ke database."""
        if not self.session:
            raise RuntimeError("Session belum dimulai! Gunakan 'async with uow'.")
        await self.session.commit()

    async def rollback(self) -> None:
        """Batalkan perubahan."""
        if self.session:
            await self.session.rollback()