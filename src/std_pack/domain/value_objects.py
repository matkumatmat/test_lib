"""
Domain Value Objects.
Objek immutable yang didefinisikan oleh atributnya, bukan identitasnya.
"""
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict

# Generic type untuk self-referencing
V = TypeVar("V", bound="BaseValueObject")

class BaseValueObject(BaseModel):
    """
    Base class untuk Value Object.
    Sifat:
    1. Immutable (frozen=True)
    2. Equality berdasarkan nilai atribut (bukan memori/ID)
    """
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseValueObject):
            return self.model_dump() == other.model_dump()
        return False