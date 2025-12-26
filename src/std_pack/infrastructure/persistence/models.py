# src/std_pack/infrastructure/persistence/models.py

import uuid6
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

# Helper kecil agar tidak nulis lambda panjang-panjang
def utc_now_aware():
    return datetime.now(timezone.utc)

class BaseDBModel(DeclarativeBase):
    """
    Base Class untuk SEMUA model database di dalam ekosistem ini.
    
    Fitur Standar:
    1. UUID sebagai Primary Key (Wajib).
    2. Timestamps otomatis (created_at, updated_at).
    3. Abstract (tidak membuat tabel sendiri).
    """
    __abstract__ = True  # Mencegah SQLAlchemy membuat tabel 'base_db_model'

    # Definisi Ulang ID & Timestamp (Mirroring dari Domain Entity)
    # Kita wajib mendefinisikan ini agar SQLAlchemy tahu cara membuat DDL SQL.
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        index=True,
        nullable=False,
        # Default di DB level (jaga-jaga jika insert manual via SQL client)
        default=uuid6.uuid7
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now_aware,
        server_default=func.now() # Menggunakan jam server database
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now_aware,
        onupdate=utc_now_aware,
        server_default=func.now()
    )

class SoftDeleteMixin:
    """
    Mixin untuk fitur Soft Delete (Menandai dihapus tanpa menghilangkan baris).
    Gunakan ini di model konkret: class User(BaseDBModel, SoftDeleteMixin): ...
    """
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        server_default="false",
        nullable=False
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

class AuditMixin:
    """
    Mixin untuk mencatat SIAPA yang membuat/mengubah data.
    Biasanya diisi oleh Middleware atau Repository saat save.
    """
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )