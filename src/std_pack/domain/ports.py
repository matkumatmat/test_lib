"""
Domain Ports.
Hanya berisi kontrak yang DI-BUTUH-KAN oleh Domain Logic (misal: Domain Service).
"""
from typing import Any, Protocol, TypeVar

from .entities import BaseEntity

T = TypeVar("T", bound=BaseEntity)

class IRepository(Protocol[T]):
    """
    Port: Generic Repository Interface.
    Didefinisikan di Domain karena Domain Service mungkin butuh baca data.
    """
    async def get(self, id: Any) -> T | None: ... # pragma: no cover
    async def save(self, entity: T) -> T: ... # pragma: no cover
    async def delete(self, id: Any) -> bool: ... # pragma: no cover
    
    async def list(
        self, 
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[T]: ... # pragma: no cover
    
    async def count(self, filters: dict[str, Any] | None = None) -> int: ... # pragma: no cover