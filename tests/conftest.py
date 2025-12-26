# tests/conftest.py

import pytest
# import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from std_pack.infrastructure.persistence.models import BaseDBModel

# Gunakan SQLite in-memory untuk tes cepat, atau Postgres Docker untuk real test
# URL = "postgresql+asyncpg://user:pass@localhost:5432/test_db"
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# @pytest.fixture(scope="session")
# def event_loop():
#     """Create an instance of the default event loop for each test case."""
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback() # Rollback setelah tiap tes agar data bersih