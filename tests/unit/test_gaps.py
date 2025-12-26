import pytest
import uuid
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository
from std_pack.infrastructure.persistence.uow import SqlAlchemyUnitOfWork
from std_pack.infrastructure.events.memory import MemoryMessageBus
from std_pack.domain.events import DomainEvent
from std_pack.domain.exceptions import DomainException 
# Import exception lain jika ada, misal EntityNotFoundException

# --- Setup Dummy untuk Repo ---
from std_pack.domain.entities import BaseEntity
from std_pack.infrastructure.persistence.models import BaseDBModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import async_sessionmaker
from std_pack.config.settings import BaseAppSettings, EnvironmentType

class GapEntity(BaseEntity):
    name: str

class GapModel(BaseDBModel):
    __tablename__ = "gap_test"
    name: Mapped[str]

# --- TEST REPOSITORY EDGE CASES ---
@pytest.mark.asyncio
async def test_repo_edge_cases(db_session, db_engine):
    # Setup Table
    async with db_engine.begin() as conn:
        await conn.run_sync(GapModel.metadata.create_all)

    repo = SqlAlchemyRepository(db_session, GapEntity, GapModel)

    # 1. Test Count (Missing coverage di 'count')
    count_awal = await repo.count()
    assert count_awal == 0

    await repo.save(GapEntity(name="A"))
    count_akhir = await repo.count()
    assert count_akhir == 1

    # 2. Test Delete Not Found (Missing coverage di 'return False')
    random_id = uuid.uuid4()
    result = await repo.delete(random_id)
    assert result is False  # Harus False, bukan error

# --- TEST UOW EDGE CASES ---
@pytest.mark.asyncio
async def test_uow_error_usage(db_engine):
    session_factory = async_sessionmaker(db_engine)
    uow = SqlAlchemyUnitOfWork(session_factory)

    # 1. Test Commit tanpa 'async with' (Missing coverage 'raise RuntimeError')
    with pytest.raises(RuntimeError):
        await uow.commit()

# --- TEST MEMORY BUS ERROR HANDLING ---
class BrokenEvent(DomainEvent):
    pass

@pytest.mark.asyncio
async def test_bus_handler_failure(capsys): # <--- GANTI 'caplog' JADI 'capsys'
    """Test handler yang error tidak bikin crash aplikasi."""
    bus = MemoryMessageBus()

    # Handler yang sengaja error
    def broken_handler(event: BrokenEvent):
        raise ValueError("Boom!")

    bus.subscribe(BrokenEvent, broken_handler)

    # Publish harusnya GAK raise error (karena di-try-except di memory.py)
    # Tapi dia harus logging error ke STDOUT
    await bus.publish(BrokenEvent())

    # Tangkap output stdout (layar)
    captured = capsys.readouterr()
    
    # Assert log error muncul di output yang tertangkap
    assert "event_handler_failed" in captured.out
    assert "Boom!" in captured.out

# --- TEST EXCEPTIONS ---
def test_exceptions_instantiation():
    """Memanggil semua exception custom agar terbaca coverage."""
    # Instansiasi dasar
    exc = DomainException("General Error")
    assert str(exc) == "General Error"

    # Jika Anda punya exception lain di domain/exceptions.py, panggil disini
    # misal: 
    # exc2 = EntityNotFoundException("User not found")
    # assert exc2.message == "User not found"

from std_pack.domain.exceptions import (
    EntityNotFoundError, 
    EntityAlreadyExistsError,
    BusinessRuleViolationError,
    UnauthorizedError,
    ForbiddenError,
    TooManyRequestsError
)

def test_all_custom_exceptions():
    """Memastikan semua __init__ exception terpanggil."""
    
    # 1. EntityNotFoundError
    e1 = EntityNotFoundError(entity_name="User", entity_id=123)
    assert "User" in str(e1)
    assert "123" in str(e1)
    assert e1.code == "USER_NOT_FOUND"

    # 2. EntityAlreadyExistsError
    e2 = EntityAlreadyExistsError(entity_name="Email", field="address", value="a@b.com")
    assert "a@b.com" in str(e2)
    assert e2.code == "EMAIL_ALREADY_EXISTS"

    # 3. BusinessRuleViolationError
    e3 = BusinessRuleViolationError("Stok habis")
    assert e3.code == "BUSINESS_RULE_VIOLATION"

    # 4. UnauthorizedError
    e4 = UnauthorizedError()
    assert e4.code == "DOMAIN_UNAUTHORIZED"

    # 5. ForbiddenError
    e5 = ForbiddenError()
    assert e5.code == "ACCESS_FORBIDDEN"

    # 6. TooManyRequestsError
    e6 = TooManyRequestsError(retry_after=60)
    assert "60" in str(e6)
    assert e6.retry_after == 60    

@pytest.mark.asyncio
async def test_uow_defensive_logic(db_engine):
    session_factory = async_sessionmaker(db_engine)
    uow = SqlAlchemyUnitOfWork(session_factory)

    # 1. Test Rollback saat Session None (Safety Check)
    # Ini akan cover baris "if self.session:" di method rollback
    await uow.rollback() 
    # Assert tidak error (silent pass)

    # 2. Test __aexit__ tanpa session (Safety Check)
    # Panggil __aexit__ manual seolah-olah context manager selesai tapi session gagal init
    await uow.__aexit__(None, None, None)
    # Assert tidak error    

# --- TEST SETTINGS ---
def test_settings_is_production():
    """Cover property is_production di settings.py"""
    # Default (LOCAL)
    settings = BaseAppSettings()
    assert settings.is_production is False
    
    # Production
    settings.ENVIRONMENT = EnvironmentType.PRODUCTION
    assert settings.is_production is True

# --- TEST BUS ADDITIONAL ---
@pytest.mark.asyncio
async def test_bus_publish_batch_and_no_handler():
    bus = MemoryMessageBus()
    
    # 1. Test Publish tanpa Subscriber (Cover 'if handlers:' else path)
    # Tidak boleh error, cuma log info/debug
    await bus.publish(BrokenEvent()) 

    # 2. Test Publish Batch (Cover method publish_batch)
    received = []
    bus.subscribe(BrokenEvent, lambda e: received.append(e))
    
    events = [BrokenEvent(), BrokenEvent()]
    await bus.publish_batch(events)
    
    assert len(received) == 2

# --- TEST UOW MANUAL ROLLBACK ---
@pytest.mark.asyncio
async def test_uow_manual_rollback_with_session(db_engine):
    """Cover pemanggilan rollback() manual saat session aktif."""
    session_factory = async_sessionmaker(db_engine)
    uow = SqlAlchemyUnitOfWork(session_factory)

    # Buka session manual
    await uow.__aenter__()
    assert uow.session is not None
    
    # Panggil rollback manual (bukan via exit exception)
    # Ini akan meng-cover baris 'await self.session.rollback()'
    await uow.rollback()
    
    # Tutup
    await uow.__aexit__(None, None, None)    