# src/std_pack/bootstrap/lifespan.py

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from std_pack.infrastructure.persistence.database import DatabaseManager
from std_pack.infrastructure.logging import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def standard_lifespan(
    app: FastAPI, 
    db_manager: DatabaseManager
) -> AsyncGenerator[None, None]:
    """
    Helper lifespan standar.
    Aplikasi pengguna bisa menggunakan ini atau membungkusnya.
    
    Fungsi:
    1. Inisialisasi Database Connection Pool saat startup.
    2. Menutup koneksi saat shutdown.
    """
    
    # --- STARTUP ---
    try:
        logger.info("application_startup")
        db_manager.init_db()
    except Exception as e:
        logger.critical("startup_failed", error=str(e))
        raise e
        
    yield
    
    # --- SHUTDOWN ---
    logger.info("application_shutdown")
    await db_manager.close()