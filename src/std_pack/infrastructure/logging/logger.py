"""
Infrastructure Logging Implementation.
Menyediakan setup structlog yang production-ready dengan JSON format,
interception standard logging, dan handling context async.
"""
import logging
import sys
from typing import Any

import structlog
from std_pack.config import BaseAppSettings

def setup_logging(settings: BaseAppSettings) -> None:
    """
    Konfigurasi global logging.
    Wajib dipanggil di awal startup aplikasi (main.py).
    """
    
    # 1. Tentukan Processor (Pipeline pemrosesan log)
    shared_processors = [
        structlog.contextvars.merge_contextvars, # Ambil request_id dkk
        structlog.processors.add_log_level,      # Tambah field 'level': 'info'
        structlog.processors.TimeStamper(fmt="iso", utc=True), # Waktu UTC ISO 8601
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            }
        ),
    ]

    if settings.is_production:
        # PRODUCTION: Format JSON Machine Readable
        processors = shared_processors + [
            structlog.processors.dict_tracebacks, # Error jadi object JSON, bukan text
            structlog.processors.JSONRenderer(),  # Render ke JSON string
        ]
    else:
        # DEVELOPMENT: Format Console Cantik (Human Readable)
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]

    # 2. Konfigurasi Structlog
    structlog.configure(
        processors=processors, # type: ignore
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            _get_logging_level(settings.LOG_LEVEL)
        ),
        cache_logger_on_first_use=True,
    )

    # 3. Intercept & Konfigurasi Standard Library Logging
    _configure_standard_logging(processors, settings.LOG_LEVEL)


def get_logger(name: str | None = None) -> Any:
    """Helper untuk mengambil logger di modul lain."""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


def _get_logging_level(level_str: str) -> int:
    return getattr(logging, level_str.upper(), logging.INFO)


def _configure_standard_logging(processors: list[Any], level_str: str):
    """
    Mengatur logging bawaan Python (termasuk Uvicorn & SQLAlchemy)
    agar output-nya seragam dengan structlog.
    """
    handler = logging.StreamHandler(sys.stdout)
    
    # Gunakan StructlogFormatter untuk membungkus log standar menjadi format kita
    # Ini trik agar log dari library lain (uvicorn, db) tetap JSON
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer() if isinstance(processors[-1], structlog.processors.JSONRenderer) else structlog.dev.ConsoleRenderer(),
        ],
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(_get_logging_level(level_str))

    # --- NOISE REDUCTION ---
    # Membungkam logger cerewet yang sering spam di production
    for _logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "httpcore", "httpx"]:
        logging.getLogger(_logger_name).handlers = [] # Hapus handler bawaan library
        logging.getLogger(_logger_name).propagate = True # Paksa pakai handler Root kita
    
    # Set level spesifik untuk library tertentu agar tidak bising
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)