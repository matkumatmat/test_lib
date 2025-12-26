# src/std_pack/infrastructure/persistence/repositories.py
from __future__ import annotations  # <--- TAMBAHKAN INI DI BARIS 1
from typing import Any, Type, TypeVar, Generic
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from std_pack.domain.entities import BaseEntity
from std_pack.domain.ports import IRepository

# T = Domain Entity (Pydantic)
T = TypeVar("T", bound=BaseEntity)
# M = DB Model (SQLAlchemy)
M = TypeVar("M")

class SqlAlchemyRepository(IRepository[T], Generic[T, M]):
    """
    Implementasi Repository yang menjembatani:
    Domain Entity (Pydantic) <---> Infrastructure Model (SQLAlchemy)
    """

    def __init__(
        self, 
        session: AsyncSession, 
        domain_cls: Type[T], 
        db_model_cls: Type[M]
    ):
        self.session = session
        self.domain_cls = domain_cls
        self.db_model_cls = db_model_cls

    # --- MAPPER HELPERS ---
    def _to_db(self, entity: T) -> M:
        """Mengubah Pydantic -> SQLAlchemy Model"""
        # model_dump() menghasilkan dict dari Pydantic
        return self.db_model_cls(**entity.model_dump())

    def _to_domain(self, db_obj: Any | None) -> T | None:
        """Mengubah SQLAlchemy Model -> Pydantic"""
        if not db_obj:
            return None
        # model_validate() membaca object ORM
        return self.domain_cls.model_validate(db_obj)

    # --- CRUD IMPLEMENTATION ---
    async def save(self, entity: T) -> T:
        """Create or Update (Upsert-like behavior via Merge)."""
        db_obj = self._to_db(entity)
        
        # Merge menangani insert baru atau update jika PK sudah ada
        merged_obj = await self.session.merge(db_obj)
        
        # Flush agar ID dan default values ter-generate di DB transaction
        await self.session.flush()
        
        # Kembalikan sebagai Domain Entity yang fresh
        return self._to_domain(merged_obj)

    async def get(self, id: Any) -> T | None:
        """Get by ID."""
        stmt = select(self.db_model_cls).where(self.db_model_cls.id == id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        return self._to_domain(db_obj)

    async def delete(self, id: Any) -> bool:
        """Delete by ID. Mengembalikan True jika data ditemukan & dihapus."""
        # 1. Cari dulu object-nya
        stmt = select(self.db_model_cls).where(self.db_model_cls.id == id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()

        if db_obj:
            # 2. Hapus object
            await self.session.delete(db_obj)
            await self.session.flush() # Pastikan state terkirim ke DB
            return True
        
        return False

    async def list(
        self, 
        filters: dict | None = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> list[T]:
        """List data dengan pagination sederhana."""
        stmt = select(self.db_model_cls).limit(limit).offset(offset)
        
        # TODO: Implement dynamic filtering logic here
        
        result = await self.session.execute(stmt)
        # scalars().all() mengambil semua object hasil query
        db_objs = result.scalars().all()
        
        return [self._to_domain(obj) for obj in db_objs]

    async def count(self, filters: dict | None = None) -> int:
        """Menghitung total data."""
        stmt = select(func.count()).select_from(self.db_model_cls)
        result = await self.session.execute(stmt)
        # scalar_one() untuk mengambil satu nilai int
        return result.scalar_one()

    async def save_all(self, entities: list[T]) -> list[T]:
        """
        Batch Insert/Update.
        Jauh lebih cepat daripada memanggil save() di dalam loop.
        """
        if not entities:
            return []

        # Convert semua ke DB Model
        db_objs = [self._to_db(entity) for entity in entities]
        
        # Gunakan add_all (SQLAlchemy akan mengoptimalkan insert-nya)
        # Note: merge_all tidak ada di SQLAlchemy, jadi kita pakai add_all
        # Jika butuh upsert batch, logic-nya akan lebih kompleks (tergantung DB)
        # Untuk sekarang, kita asumsikan ini Insert Baru.
        self.session.add_all(db_objs)
        
        # Flush agar ID ter-generate
        await self.session.flush()
        
        # Kembalikan list Domain Entity baru
        return [self._to_domain(obj) for obj in db_objs]        