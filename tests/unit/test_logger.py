# tests/unit/test_logger.py

import structlog
from unittest.mock import MagicMock
from std_pack.infrastructure.logging.logger import setup_logging, get_logger

def test_logger_configuration():
    """Test konfigurasi logger sederhana."""
    
    # 1. Buat Mock Settings (karena setup_logging butuh object settings)
    mock_settings = MagicMock()
    mock_settings.LOG_LEVEL = "DEBUG"
    # Simulasi mode development (is_production = False) -> Console Renderer
    mock_settings.is_production = False 
    
    # 2. Panggil fungsi setup dengan parameter yang benar
    setup_logging(settings=mock_settings)
    
    # 3. Verify logger berfungsi
    logger = get_logger() # Pakai helper get_logger dari modul
    logger.info("test_log", status="ok")
    
    # 4. Cek apakah structlog sudah terkonfigurasi
    assert structlog.is_configured()

def test_logger_production_mode():
    """Test konfigurasi logger mode production (JSON)."""
    mock_settings = MagicMock()
    mock_settings.LOG_LEVEL = "INFO"
    mock_settings.is_production = True # Simulasi Production -> JSON Renderer
    
    setup_logging(settings=mock_settings)
    
    # Pastikan tidak crash saat dipanggil
    logger = get_logger()
    logger.info("prod_log", status="json")
    
    assert structlog.is_configured()