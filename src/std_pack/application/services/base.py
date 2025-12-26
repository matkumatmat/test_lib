"""
Base Application Services.
Menyediakan logika CRUD generik untuk mempercepat development microservices.
"""
from typing import Any, Generic, TypeVar

from std_pack.domain.entities import BaseEntity
from std_pack.domain.exceptions import EntityNotFoundError
from std_pack.domain.ports import IRepository
from std_pack.application.interfaces.ports import IUnitOfWork

# Generic Types
EntityT = TypeVar("EntityT", bound=BaseEntity)


class BaseCrudService(Generic[EntityT]):
    """
    Service Generik untuk operasi CRUD standar.
    
    Cara Pakai di Microservice:
    class UserService(BaseCrudService[User]):
        def __init__(self, repo: UserRepository, uow: IUnitOfWork):
            super().__init__(repo, uow)
    """

    def __init__(
        self, 
        repository: IRepository[EntityT], 
        uow: IUnitOfWork
    ):
        self.repository = repository
        self.uow = uow

    async def get(self, id: Any) -> EntityT:
        """
        Ambil satu data. Error jika tidak ketemu.
        """
        entity = await self.repository.get(id)
        if not entity:
            # Menggunakan nama class dari Generic Type untuk pesan error
            entity_name = self._get_entity_name()
            raise EntityNotFoundError(entity_name, id)
        return entity

    async def list(
        self, 
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 20
    ) -> tuple[list[EntityT], int]:
        """
        Ambil list data + total count (untuk pagination).
        Return: (items, total_count)
        """
        offset = (page - 1) * size
        
        # Parallel execution bisa dioptimalkan nanti, 
        # saat ini sequential demi kestabilan.
        items = await self.repository.list(filters, limit=size, offset=offset)
        total = await self.repository.count(filters)
        
        return items, total

    async def create(self, entity: EntityT) -> EntityT:
        """
        Create data baru dengan Transaction Atomicity.
        """
        async with self.uow:
            saved_entity = await self.repository.save(entity)
            await self.uow.commit()
            return saved_entity

    async def update(self, id: Any, **changes: Any) -> EntityT:
        """
        Update data dengan metode Patch (hanya field yang berubah).
        """
        async with self.uow:
            # 1. Fetch Existing
            entity = await self.get(id)
            
            # 2. Update Field di Memory
            # (Menggunakan setattr atau Pydantic copy)
            updated_data = entity.model_dump()
            updated_data.update(changes)
            
            # Validasi ulang dengan Pydantic
            new_entity = entity.model_validate(updated_data)
            
            # 3. Save & Commit
            saved_entity = await self.repository.save(new_entity)
            await self.uow.commit()
            return saved_entity

    async def delete(self, id: Any) -> None:
        """
        Hapus data permanen.
        """
        async with self.uow:
            # Cek dulu ada atau tidak (opsional, tergantung kebutuhan performa)
            # await self.get(id) 
            
            success = await self.repository.delete(id)
            if not success:
                 entity_name = self._get_entity_name()
                 raise EntityNotFoundError(entity_name, id)
            
            await self.uow.commit()

    def _get_entity_name(self) -> str:
        """Helper untuk ambil nama entity (untuk pesan error)."""
        # Hack sedikit untuk dapat nama class dari Generic T
        # Bisa di-override oleh child class
        try:
            return self.__orig_class__.__args__[0].__name__ # type: ignore
        except (AttributeError, IndexError):
            return "Entity"