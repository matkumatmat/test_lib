"""
Base Data Transfer Objects.
Menyediakan struktur standar untuk input/output API.
Menggunakan Generics untuk Pagination.
"""
from typing import Generic, TypeVar, Any

from pydantic import BaseModel, ConfigDict

# Generic Type untuk item dalam pagination (misal: list[UserDTO])
DataT = TypeVar("DataT")


class BaseDTO(BaseModel):
    """
    Parent class untuk semua DTO.
    Mengaktifkan from_attributes (orm_mode di Pydantic v1) 
    agar bisa convert langsung dari Entity/Model DB.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class PaginatedResponse(BaseDTO, Generic[DataT]):
    """
    Standar Output untuk List Data dengan Pagination.
    Frontend akan sangat terbantu dengan format yang konsisten ini.
    """
    items: list[DataT]
    total: int
    page: int
    size: int
    pages: int  # Total halaman

    @classmethod
    def create(
        cls, 
        items: list[DataT], 
        total: int, 
        page: int, 
        size: int
    ) -> "PaginatedResponse[DataT]":
        """Factory method untuk menghitung total pages otomatis."""
        import math
        pages = math.ceil(total / size) if size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

class ErrorResponse(BaseDTO):
    """Standar output jika terjadi error."""
    code: str
    message: str
    details: dict[str, Any] | None = None    