# tests/flow/test_registration_flow.py
import pytest
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

# --- LIBRARY COMPONENT ---
from std_pack.infrastructure.persistence.uow import SqlAlchemyUnitOfWork
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository
from std_pack.infrastructure.events.memory import MemoryMessageBus
from std_pack.infrastructure.security.password import hash_password
from std_pack.domain.entities import BaseEntity
from std_pack.domain.events import DomainEvent
from std_pack.infrastructure.persistence.models import BaseDBModel
from sqlalchemy.orm import Mapped, mapped_column

# --- 1. SETUP DUMMY CONTEXT (Simulasi App Layer) ---
# Kita butuh Entity User & Event UserCreated
class User(BaseEntity):
    username: str
    email: str
    password_hash: str

class UserCreatedEvent(DomainEvent):
    user_id: str
    email: str

# Kita butuh DB Model
class UserModel(BaseDBModel):
    __tablename__ = "flow_users"
    username: Mapped[str]
    email: Mapped[str]
    password_hash: Mapped[str]

# --- 2. SKENARIO UTAMA: REGISTER USER ---
@pytest.mark.asyncio
async def test_flow_user_registration_journey(db_engine):
    """
    E2E Logic Test:
    Input DTO -> Service Logic -> Hashing -> DB Save (UoW) -> Event Publish -> Handler React
    """
    
    # A. INFRASTRUCTURE SETUP
    # 1. Siapkan Database
    async with db_engine.begin() as conn:
        await conn.run_sync(UserModel.metadata.create_all)
    
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    
    # 2. Siapkan Bus & Handler (Background Process)
    bus = MemoryMessageBus()
    email_sent_flag = [] # Jebakan untuk cek apakah handler jalan

    async def send_welcome_email(event: UserCreatedEvent):
        # Simulasi kirim email
        print(f">> [MAILER] Sending email to {event.email}")
        email_sent_flag.append(event.email)

    bus.subscribe(UserCreatedEvent, send_welcome_email)

    # B. SIMULASI APPLICATION SERVICE (The "Register" Logic)
    # Anggap ini adalah kode di dalam 'AuthService.register()'
    async def execute_register_service(input_data: dict):
        uow = SqlAlchemyUnitOfWork(session_factory)
        
        async with uow:
            # 1. Init Repo
            repo = SqlAlchemyRepository(uow.session, User, UserModel)
            
            # 2. Domain Logic: Hash Password
            hashed = hash_password(input_data["password"])
            
            # 3. Create Entity
            new_user = User(
                username=input_data["username"],
                email=input_data["email"],
                password_hash=hashed
            )
            
            # 4. Save to DB
            saved_user = await repo.save(new_user)
            
            # 5. Publish Event (Domain Event)
            event = UserCreatedEvent(
                user_id=str(saved_user.id),
                email=saved_user.email
            )
            await bus.publish(event)
            
            # 6. Commit Transaction
            await uow.commit()
            
            return saved_user

    # C. EXECUTION (ACT)
    raw_input = {
        "username": "kayez_dev",
        "email": "kayez@example.com",
        "password": "SuperSecretPassword123!"
    }
    
    result_user = await execute_register_service(raw_input)

    # D. VERIFICATION (ASSERT)
    
    assert result_user.username == "kayez_dev"
    assert result_user.password_hash != "SuperSecretPassword123!" 
    
    # 2. Cek Database Fisik (Persistence Check)
    async with db_engine.connect() as conn:
        stmt = select(UserModel).where(UserModel.email == "kayez@example.com")
        
        # PERBAIKAN DISINI:
        # Gunakan .first() agar dapat satu baris penuh (Row object)
        result = await conn.execute(stmt)
        row = result.first()
        
        assert row is not None, "User harus tersimpan di DB!"
        
        # Row object di SQLAlchemy Core bisa diakses via attribute name
        assert row.username == "kayez_dev"
        assert row.password_hash.startswith("$2b$")
        
    # 3. Cek Side Effect (Event Handler)
    # Karena bus publish async, mungkin butuh waktu sepersekian detik
    await asyncio.sleep(0.01)
    
    assert len(email_sent_flag) == 1
    assert email_sent_flag[0] == "kayez@example.com"