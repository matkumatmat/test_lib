
import pytest
import uuid
import asyncio
from datetime import datetime
from sqlmodel import SQLModel, Field, select
from typing import AsyncGenerator

# --- Real Modules Import ---
from std_pack.config.settings import BaseAppSettings
from std_pack.infrastructure.persistence.database import DatabaseManager
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository
from std_pack.infrastructure.persistence.uow import SqlAlchemyUnitOfWork
from std_pack.infrastructure.security.password import hash_password, verify_password
from std_pack.infrastructure.security.token import TokenHelper
from std_pack.domain.entities import BaseEntity
from std_pack.domain.exceptions import EntityNotFoundError

# --- 1. SETUP: Real Implementation Definitions ---

# Mocking Settings but strictly using Pydantic validation (not MagicMock)
class IntegrationSettings(BaseAppSettings):
    SECRET_KEY: str = "integration-test-secret-key-12345"
    # Using memory SQLite but simulating proper asyncpg flow via code path
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    REDIS_URL: str = "redis://localhost:6379/0"

# Domain Entity
class User(BaseEntity):
    email: str
    password_hash: str
    full_name: str
    is_active: bool = True

# Database Model
class UserModel(SQLModel, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    full_name: str
    is_active: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Repository Implementation
class UserRepository(SqlAlchemyRepository[User, UserModel]):
    def __init__(self, session):
        super().__init__(session, domain_cls=User, db_model_cls=UserModel)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(UserModel).where(UserModel.email == email)
        # FIX: Back to .exec() because we now use SQLModel AsyncSession correctly
        result = await self.session.exec(statement)
        instance = result.first()
        if instance:
            return self._to_domain(instance)
        return None

# --- 2. INTEGRATION TEST: Full Flow ---

@pytest.fixture
async def real_db_manager():
    """Spin up a REAL DatabaseManager with SQLite (closest we can get to PG without container)."""
    settings = IntegrationSettings()
    manager = DatabaseManager(url=settings.DATABASE_URL, echo=True) # Echo=True to check syntax
    manager.init_db()

    # Manually create tables
    async with manager.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield manager

    await manager.close()

@pytest.mark.asyncio
async def test_full_application_flow(real_db_manager):
    """
    Tests the full flow:
    Settings -> DB Connect -> Repo -> UOW -> Security -> Save -> Load -> Auth
    """
    settings = IntegrationSettings()

    # 1. Security: Hash Password
    raw_password = "SecurePassword123!"
    hashed_password = hash_password(raw_password)
    assert hashed_password != raw_password
    assert verify_password(raw_password, hashed_password)

    # 2. Persistence: Unit of Work & Repository
    # Simulate a Service Layer operation

    new_user_id = None

    # -- OPERATION 1: Create User via UOW --
    # FIX: UOW expects a session_factory, NOT an active session.
    # It manages its own session lifecycle.
    uow = SqlAlchemyUnitOfWork(real_db_manager.session_factory)

    async with uow:
        # Repository must be initialized with the UOW's active session
        user_repo = UserRepository(uow.session)

        # Create Domain Object
        new_user = User(
            email="tester@example.com",
            password_hash=hashed_password,
            full_name="Integration Tester"
        )

        # Save
        saved_user = await user_repo.save(new_user)
        new_user_id = saved_user.id

        await uow.commit() # Real commit

    assert new_user_id is not None

    # -- OPERATION 2: Authenticate User (Read) --
    async with real_db_manager.session_factory() as session:
        user_repo = UserRepository(session)

        # Simulate Login: Fetch by email
        fetched_user = await user_repo.get_by_email("tester@example.com")

        assert fetched_user is not None
        assert fetched_user.full_name == "Integration Tester"

        # Verify Password again from DB data
        assert verify_password(raw_password, fetched_user.password_hash)

        # Generate Token using Real TokenHelper
        token_helper = TokenHelper(settings)

        access_token = token_helper.create_access_token(
            subject=str(fetched_user.id),
            email=fetched_user.email,
            role="admin"
        )

        assert access_token is not None

        # Decode Token
        payload = token_helper.decode_token(access_token)
        assert payload["sub"] == str(fetched_user.id)
        assert payload["email"] == "tester@example.com"
        assert payload["role"] == "admin"

    # -- OPERATION 3: Update User --
    uow_update = SqlAlchemyUnitOfWork(real_db_manager.session_factory)

    async with uow_update:
        user_repo = UserRepository(uow_update.session)
        user_to_update = await user_repo.get(new_user_id)

        # Ensure object is attached to current session or re-fetched
        # Since 'get' attaches it, we are good.
        user_to_update.full_name = "Changed Name"

        await user_repo.save(user_to_update)
        await uow_update.commit()

    # -- OPERATION 4: Verify Update --
    async with real_db_manager.session_factory() as session:
        user_repo = UserRepository(session)
        updated_user = await user_repo.get(new_user_id)
        assert updated_user.full_name == "Changed Name"
