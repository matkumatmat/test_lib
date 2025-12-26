"""
Domain Entities (Pure Pydantic).
Menggunakan UUIDv7 untuk performa database yang optimal (Sequential Indexing).
"""

import uuid
from datetime import datetime, timezone
from uuid6 import uuid7
from pydantic import BaseModel, ConfigDict, Field

def utc_now() -> datetime:
    """
    helper waktu utc (self-contained)
    """
    return datetime.now(timezone.utc)

class BaseEntity(BaseModel):
    """
    Parent class untuk semua domain entity
    menggunakan uuid7 dengan polyfill dari uuid6 (keterbatasan versi python)
    !!!upgrade python kedepannya untuk skalabilitas ya hehe!!! python^3.13
    """
    id : uuid.UUID = Field(
        default_factory=uuid7
    )
    created_at : datetime = Field(
        default_factory=utc_now
    )
    updated_at : datetime = Field(
        default_factory=utc_now
    )

    model_config = ConfigDict(
        from_attributes= True,
        validate_assignment= True,
        # json_encoders={datetime:lambda v: v.isoformat()}
    )

    def __eq__(
            self, 
            other: object
        ) -> bool:
        """Entity dianggap sama jika ID-nya sama."""
        if isinstance(
            other, 
            BaseEntity
        ):
            return self.id == other.id
        return False
    
class SoftDeleteMixin(BaseModel):
    """
    Mixin logis untuk soft delete.
    Hanya berisi data dan behavior domain, bukan implementasi DB.
    """
    is_deleted: bool = False
    deleted_at: datetime | None = None

    def mark_deleted(self) -> None:
        """Domain logic untuk menghapus."""
        self.is_deleted = True
        self.deleted_at = utc_now()

    def restore(self) -> None:
        """Domain logic untuk restore."""
        self.is_deleted = False
        self.deleted_at = None

class AuditMixin(BaseModel):
    """
    Mixin logis untuk audit user.
    Menggunakan string agar agnostik terhadap tipe ID User (Int/UUID).
    """
    created_by: str | None = None
    updated_by: str | None = None        

