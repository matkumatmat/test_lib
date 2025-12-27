"""
Unit of Work Implementation.
Menangani transaksi database menggunakan SQLAlchemy/SQLModel Session.
Menghubungkan Application Layer (IUnitOfWork) dengan Infrastructure (Database).
"""
from typing import Type, Any

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from std_pack.application.interfaces.ports import IUnitOfWork


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """
    Implementasi Unit of Work untuk SQLAlchemy/SQLModel.
    
    Supports two modes:
    1. Factory Mode: Provide `session_factory`. UOW manages session lifecycle (create & close).
    2. Session Mode: Provide `session`. UOW uses existing session (does NOT close it).
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None
    ):
        if not session_factory and not session:
             raise ValueError("Must provide either session_factory or session")

        self.session_factory = session_factory
        self.session = session
        self._is_external_session = session is not None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        """Mulai transaksi baru (Start Transaction)."""
        if not self._is_external_session and self.session_factory:
            self.session = self.session_factory()

        if not self.session:
            raise RuntimeError("Session initialization failed.")

        return self

    async def __aexit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, traceback: Any) -> None:
        """Selesai transaksi (End Transaction)."""
        if self.session:
            if exc_type:
                # Jika terjadi error di dalam blok 'async with', rollback otomatis
                await self.rollback()
            
            # Hanya tutup jika kita yang membuat session (Factory Mode)
            if not self._is_external_session:
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
