"""
Domain events module
menggunakan pydantic v2 untuk validasi
dan immutability
"""

from uuid6 import uuid7
import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar
from pydantic import BaseModel, ConfigDict, Field

class DomainEvent(BaseModel):
    """
    Base class untuk semua domain events.
    Events bersifat immutable (frozen) karena merepresentasikan fakta masa lalu.
    """
    event_id : uuid.UUID = Field(
        default_factory=uuid7
    )
    occurred_at : datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    event_type: ClassVar[str]
    model_config = ConfigDict(
        frozen= True,
        arbitrary_types_allowed=True,
        json_encoders={datetime : lambda v: v.isoformat()}
    )

    def __init_subclass__(cls, **kwargs):
        """Otomatis set event_type sesuai nama class"""        
        super().__init_subclass__(**kwargs)
        cls.event_type = cls.__name__

# ----- Standard CRUD Events -------        

class EntityCreatedEvent(DomainEvent):
    """Event saat entitas berhasil dibuat."""
    entity_type : str
    entity_id : Any
    payload : dict[str, Any] = Field(
        default_factory=dict
    )

class EntityUpdatedEvent(DomainEvent):
    """Event saat entitas di perbarui"""
    entity_type : str
    entity_id : Any
    changes : dict[str, Any]

class EntityDeletedEvent(DomainEvent):
    """Event saat entitas di hapus (hard/soft delete)"""
    entity_type : str
    entity_id : Any