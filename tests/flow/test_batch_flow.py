import pytest
import time
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

# Import komponen library
from std_pack.infrastructure.persistence.uow import SqlAlchemyUnitOfWork
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository
from std_pack.domain.entities import BaseEntity
from std_pack.infrastructure.persistence.models import BaseDBModel
from sqlalchemy.orm import Mapped, mapped_column

# --- SETUP DUMMY PRODUCT ---
class Product(BaseEntity):
    sku: str
    price: int

class ProductModel(BaseDBModel):
    __tablename__ = "batch_products"
    sku: Mapped[str]
    price: Mapped[int]

# --- TEST BATCH INSERT ---
@pytest.mark.asyncio
async def test_flow_batch_insert_performance(db_engine):
    """
    Test kemampuan insert massal (Batch Upload).
    Skenario: Upload 1000 produk sekaligus.
    """
    # 1. Setup DB
    async with db_engine.begin() as conn:
        await conn.run_sync(ProductModel.metadata.create_all)
    
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    uow = SqlAlchemyUnitOfWork(session_factory)

    # 2. Siapkan Data Dummy (1000 items)
    bulk_data = [
        Product(sku=f"SKU-{i}", price=i*100) 
        for i in range(1000)
    ]

    # 3. Eksekusi Batch Save
    start_time = time.time()
    
    async with uow:
        repo = SqlAlchemyRepository(uow.session, Product, ProductModel)
        
        # Panggil method baru kita
        saved_items = await repo.save_all(bulk_data)
        
        await uow.commit()
    
    duration = time.time() - start_time
    print(f"\n>> Waktu Insert 1000 Data: {duration:.4f} detik")

    # 4. Verifikasi
    assert len(saved_items) == 1000
    assert saved_items[0].id is not None # ID harus ter-generate otomatis
    
    # Cek jumlah di DB
    async with db_engine.connect() as conn:
        count = await conn.scalar(select(func.count()).select_from(ProductModel))
        assert count == 1000