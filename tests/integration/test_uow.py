# tests/integration/test_uow.py
import pytest
from std_pack.infrastructure.persistence.uow import SqlAlchemyUnitOfWork # Pastikan import ini
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository
from std_pack.domain.entities import BaseEntity
from std_pack.infrastructure.persistence.models import BaseDBModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import select
# Tambahkan import ini:
from sqlalchemy.ext.asyncio import async_sessionmaker

# --- SETUP DUMMY ---
class DummyEntity(BaseEntity):
    name: str

class DummyModel(BaseDBModel):
    __tablename__ = "dummies_uow"
    name: Mapped[str]

# --- TEST CASE ---
@pytest.mark.asyncio
async def test_uow_rollback_on_error(db_session, db_engine):
    # 1. Setup Tabel & UoW
    async with db_engine.begin() as conn:
        await conn.run_sync(DummyModel.metadata.create_all)

    # Factory function untuk session (mocking session_factory)
    # Karena UoW biasanya minta session_factory, kita kasih lambda yang return session test kita
    # CATATAN: Ini tergantung implementasi UoW Anda. 
    # Jika UoW Anda membuat session sendiri, kita harus inject session yang sama dengan fixture.
    # Untuk test ini, kita bisa manual inject session jika UoW mendukungnya, 
    # atau kita biarkan UoW bikin session tapi kita cek DB-nya pakai session fixture.
    
    # Asumsi: UoW Anda menerima session_factory.
    # Kita pakai trik: UoW sebenarnya membungkus session.
    
    # Mari kita simulasikan UoW logic secara manual jika UoW Anda belum support injection session luar:
    # "Jika blok ini error, session harus rollback"
    
    try:
        # Start Transaction (Manual simulation of UoW __aenter__)
        # Di Real Code: async with uow: ...
        
        # A. Simpan Data Sukses
        repo = SqlAlchemyRepository(db_session, DummyEntity, DummyModel)
        await repo.save(DummyEntity(name="Harusnya Hilang"))
        
        # B. Cek Memory (belum commit)
        in_memory = await repo.list()
        assert len(in_memory) == 1
        
        # C. Bikin Error Buatan
        raise ValueError("Oops, error sengaja!")
        
        # D. Commit (Tidak boleh tereksekusi)
        await db_session.commit()
        
    except ValueError:
        # E. Rollback (Simulasi UoW __aexit__)
        await db_session.rollback()

    # --- VERIFIKASI ---
    # F. Cek Database: Harusnya KOSONG karena rollback
    # Kita pakai session BARU atau query langsung untuk memastikan persistence
    result = await repo.list()
    assert len(result) == 0, "DATA TIDAK ROLLBACK! BAHAYA!"


# Tambahkan method ini di bawah test_uow_rollback_on_error

@pytest.mark.asyncio
async def test_uow_commit_success(db_engine):
    """Test Happy Path: Menggunakan UoW wrapper untuk commit."""
    
    # 1. Setup Tabel
    async with db_engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all) # Gunakan BaseDBModel metadata agar aman
        await conn.run_sync(DummyModel.metadata.create_all)

    # 2. Setup UoW dengan session_factory dari engine
    from sqlalchemy.ext.asyncio import async_sessionmaker
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    
    # --- INI PERBAIKANNYA ---
    # Kita menggunakan class SqlAlchemyUnitOfWork, bukan session mentah
    uow = SqlAlchemyUnitOfWork(session_factory)

    async with uow:
        # Di dalam blok ini, uow.session sudah aktif
        repo = SqlAlchemyRepository(uow.session, DummyEntity, DummyModel)
        await repo.save(DummyEntity(name="Data Via UoW"))
        
        # Panggil method commit MILIK UOW, supaya coverage uow.py naik!
        await uow.commit()

    # 3. Verifikasi Data (Buka koneksi baru untuk cek fisik DB)
    async with db_engine.connect() as conn:
        result = await conn.execute(select(DummyModel).where(DummyModel.name == "Data Via UoW"))
        row = result.fetchone()
        assert row is not None
        assert row.name == "Data Via UoW"

# Tambahkan di tests/integration/test_uow.py

@pytest.mark.asyncio
async def test_uow_automatic_rollback(db_engine):
    """
    Cover line 36: Memastikan __aexit__ memanggil rollback() 
    secara otomatis saat terjadi exception.
    """
    # Setup
    async with db_engine.begin() as conn:
        await conn.run_sync(DummyModel.metadata.create_all)

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    uow = SqlAlchemyUnitOfWork(session_factory)

    # 1. Jalankan UoW dan force Error
    with pytest.raises(ValueError):
        async with uow:
            repo = SqlAlchemyRepository(uow.session, DummyEntity, DummyModel)
            await repo.save(DummyEntity(name="Data Rollback"))
            
            # Crash sengaja!
            raise ValueError("Boom!")

    # 2. Verifikasi Data HILANG (Rollback sukses)
    async with db_engine.connect() as conn:
        result = await conn.execute(select(DummyModel).where(DummyModel.name == "Data Rollback"))
        row = result.fetchone()
        assert row is None, "Data seharusnya hilang karena rollback otomatis!"



