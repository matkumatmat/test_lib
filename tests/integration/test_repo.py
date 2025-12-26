# tests/integration/test_repository.py

import pytest
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from std_pack.domain.entities import BaseEntity
from std_pack.infrastructure.persistence.models import BaseDBModel
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository

# --- 1. DEFINISI DUMMY (Simulasi Code Pengguna) ---

# Domain
class DummyEntity(BaseEntity):
    name: str

# Infrastructure
class DummyModel(BaseDBModel):
    __tablename__ = "dummies" # Harus beda-beda tiap tes file idealnya
    name: Mapped[str]

# --- 2. TEST CASE ---

@pytest.mark.asyncio
async def test_repository_lifecycle(db_session):
    # Setup: Create table secara manual karena ini model dinamis test
    # (Di real app, ini dihandle Alembic)
    async with db_session.bind.begin() as conn:
        await conn.run_sync(DummyModel.metadata.create_all)

    # Init Repository
    repo = SqlAlchemyRepository(
        session=db_session,
        domain_cls=DummyEntity,
        db_model_cls=DummyModel
    )

    # A. TEST CREATE (Save)
    new_data = DummyEntity(name="Test Item 1")
    saved_data = await repo.save(new_data)
    
    assert saved_data.id is not None
    assert saved_data.name == "Test Item 1"
    # Pastikan ID dari Pydantic (UUIDv7) tersimpan
    assert isinstance(saved_data.id, uuid.UUID)

    # B. TEST READ (Get)
    fetched_data = await repo.get(saved_data.id)
    
    assert fetched_data is not None
    assert fetched_data.id == saved_data.id
    assert fetched_data.name == "Test Item 1"
    assert isinstance(fetched_data, DummyEntity) # Harus kembali jadi Pydantic

    # C. TEST UPDATE
    # Ubah di domain
    fetched_data.name = "Updated Name"
    updated_data = await repo.save(fetched_data)
    
    assert updated_data.name == "Updated Name"
    assert updated_data.updated_at > saved_data.created_at # Timestamp jalan

    # D. TEST DELETE
    deleted = await repo.delete(saved_data.id)
    assert deleted is True
    
    missing = await repo.get(saved_data.id)
    assert missing is None