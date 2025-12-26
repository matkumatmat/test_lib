# tests/flow/test_ecommerce.py

import pytest
import time
import json
import uuid6 
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# --- LIBRARY IMPORTS ---
from std_pack.infrastructure.persistence.models import BaseDBModel
from std_pack.domain.entities import BaseEntity
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository
from std_pack.infrastructure.persistence.uow import SqlAlchemyUnitOfWork
from std_pack.infrastructure.security.password import hash_password, verify_password
from std_pack.infrastructure.security.token import TokenHelper
from std_pack.infrastructure.cache.redis import RedisManager
from unittest.mock import AsyncMock, MagicMock

# ... (Definisi Class User, OrderItem, dll TETAP SAMA seperti sebelumnya) ...
# Biar hemat tempat, saya asumsikan definisi class di atas tidak berubah.
# Pastikan OrderItem punya order_id: str

class User(BaseEntity):
    username: str
    password_hash: str

class OrderItem(BaseEntity):
    order_id: str 
    product_name: str
    price: int
    qty: int

class UserModel(BaseDBModel):
    __tablename__ = "users"
    username: Mapped[str]
    password_hash: Mapped[str]

class OrderModel(BaseDBModel):
    __tablename__ = "orders"
    user_id: Mapped[str]
    total_amount: Mapped[int]
    status: Mapped[str]

class OrderItemModel(BaseDBModel):
    __tablename__ = "order_items"
    order_id: Mapped[str]
    product_name: Mapped[str]
    price: Mapped[int]
    qty: Mapped[int]

class DailySalesReportModel(BaseDBModel):
    __tablename__ = "daily_reports"
    report_date: Mapped[str]
    total_sales: Mapped[int]
    total_transactions: Mapped[int]

@pytest.mark.asyncio
async def test_ecommerce_full_cycle(db_engine, capsys):
    
    # 1. Setup Engine & Session
    warehouse_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    try: # <--- BLOK TRY AGAR ENGINE SELALU DI-CLOSE
        
        # Init DBs
        async with db_engine.begin() as conn:
            await conn.run_sync(BaseDBModel.metadata.create_all)
        session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

        async with warehouse_engine.begin() as conn:
            await conn.run_sync(BaseDBModel.metadata.create_all)
        warehouse_factory = async_sessionmaker(warehouse_engine, expire_on_commit=False)

        # Mock Redis & Token (Sama)
        redis_manager = RedisManager("redis://fake") 
        mock_redis = AsyncMock()
        redis_manager.get_client = MagicMock(return_value=mock_redis)
        redis_manager.client = mock_redis
        token_helper = TokenHelper(settings=MagicMock(SECRET_KEY="rahasia", ALGORITHM="HS256", ACCESS_TOKEN_EXPIRE_MINUTES=30))

        # [1] Registration
        print("\n[1] User Registration...")
        uow = SqlAlchemyUnitOfWork(session_factory)
        async with uow:
            repo = SqlAlchemyRepository(uow.session, User, UserModel)
            hashed = hash_password("password123")
            new_user = await repo.save(User(username="kayez_buyer", password_hash=hashed))
            await uow.commit()
            user_id = str(new_user.id)
        assert user_id is not None

        # [2] Login
        print("[2] User Login...")
        assert verify_password("password123", new_user.password_hash) is True
        access_token = token_helper.create_access_token(user_id)
        assert len(access_token) > 20

        # [3] Cart
        print("[3] Adding items to Redis Cart...")
        cart_key = f"cart:{user_id}"
        items_to_buy = [
            {"product": "Laptop Gaming", "price": 15000000, "qty": 1},
            {"product": "Mouse Wireless", "price": 200000, "qty": 2},
            {"product": "Mechanical Keyboard", "price": 1000000, "qty": 1}
        ]
        redis_memory_storage = [json.dumps(item) for item in items_to_buy]
        mock_redis.lrange.return_value = redis_memory_storage
        mock_redis.delete.return_value = 1

        # [4] Checkout
        print("[4] Checkout Process (Batch Insert)...")
        async with uow:
            cart_data = await redis_manager.get_client().lrange(cart_key, 0, -1)
            parsed_items = [json.loads(item) for item in cart_data]
            total_price = sum(item["price"] * item["qty"] for item in parsed_items)
            
            order_uid_obj = uuid6.uuid7() 
            order_uid_str = str(order_uid_obj)
            
            new_order = OrderModel(id=order_uid_obj, user_id=user_id, total_amount=total_price, status="PAID")
            uow.session.add(new_order)
            
            item_repo = SqlAlchemyRepository(uow.session, OrderItem, OrderItemModel)
            domain_items = [
                OrderItem(order_id=order_uid_str, product_name=i["product"], price=i["price"], qty=i["qty"]) 
                for i in parsed_items
            ]
            
            start_time = time.time()
            await item_repo.save_all(domain_items) 
            print(f"    Batch insert {len(domain_items)} items took {time.time() - start_time:.5f}s")
            
            await redis_manager.get_client().delete(cart_key)
            await uow.commit()

        # [5] ETL
        print("[5] Running Nightly ETL Job...")
        async with session_factory() as primary_session:
            result = await primary_session.execute(select(OrderModel))
            orders = result.scalars().all()
            total_sales_today = sum(o.total_amount for o in orders)
            total_trx_today = len(orders)
        
        wh_uow = SqlAlchemyUnitOfWork(warehouse_factory)
        async with wh_uow:
            report = DailySalesReportModel(
                report_date=datetime.now().strftime("%Y-%m-%d"),
                total_sales=total_sales_today,
                total_transactions=total_trx_today
            )
            wh_uow.session.add(report)
            await wh_uow.commit()

        # [6] Verification & Cleanup
        # Gunakan Session untuk query agar dapat Object ORM
        async with warehouse_factory() as wh_session:
            result = await wh_session.execute(select(DailySalesReportModel))
            report = result.scalars().first() # scalars().first() pasti object
            
            assert report is not None
            assert report.total_sales == 16400000 
            assert report.total_transactions == 1
        
        captured = capsys.readouterr()
        assert "[1] User Registration..." in captured.out
        
        print("\n FULL E-COMMERCE FLOW SUCCESS!")

    finally:
        # CLEANUP: Tutup engine agar shell tidak macet
        await warehouse_engine.dispose()
        # db_engine diurus oleh fixture conftest, jadi aman