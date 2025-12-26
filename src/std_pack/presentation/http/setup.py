"""
HTTP Presentation Setup.
Mengatur konfigurasi level HTTP seperti CORS dan Middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from std_pack.config import BaseAppSettings

def setup_cors(app: FastAPI, settings: BaseAppSettings) -> None:
    """Setup CORS untuk mengizinkan akses dari frontend/client tertentu."""
    if settings.BACKEND_CORS_ORIGINS:
        # Konversi Pydantic List ke list of strings
        allow_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

def setup_common_middleware(app: FastAPI) -> None:
    """Setup middleware standar (GZip, dll)."""
    app.add_middleware(GZipMiddleware, minimum_size=1000)