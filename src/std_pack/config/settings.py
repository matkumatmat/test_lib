"""
Configuration Module.
Menyediakan BaseSettings yang harus diwarisi oleh aplikasi pengguna.
Menggunakan pydantic-settings.
"""
from enum import StrEnum
from typing import Literal

from pydantic import Field, AnyHttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(StrEnum):
    LOCAL = "LOCAL"
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    TESTING = "TESTING"


class BaseAppSettings(BaseSettings):
    """
    Base Configuration.
    Semua field memiliki default value agar 'safe by default',
    tapi dirancang untuk di-override via .env file.
    """
    
    # App Info
    APP_NAME: str = Field(default="StdPack Service")
    APP_VERSION: str = Field(default="0.1.0")
    
    # API Config
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: EnvironmentType = Field(default=EnvironmentType.LOCAL)
    DEBUG: bool = Field(default=False)
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    # Database (Optional karena tidak semua service pakai DB)
    DATABASE_URL: str | None = Field(default=None)

    # --- TAMBAHAN WAJIB UNTUK V2 (Cache & Rate Limit) ---
    REDIS_URL: str = Field(default="redis://localhost:6379/0") 
    # ----------------------------------------------------

    # Security
    SECRET_KEY: str = Field(default="unsafe-secret-key-change-me")
    
    @model_validator(mode="after")
    def check_safety(self) -> "BaseAppSettings":
        """Mencegah penggunaan default secret key di Production."""
        if self.ENVIRONMENT == EnvironmentType.PRODUCTION:
            if self.SECRET_KEY == "unsafe-secret-key-change-me":
                raise ValueError("CRITICAL: Do not use default SECRET_KEY in PRODUCTION!")
        return self

    # CORS (List of origins)
    # Default: Allow All (*) untuk kemudahan dev lokal
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] | list[str] = Field(default=["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Abaikan variabel .env lain agar tidak error
    )
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == EnvironmentType.PRODUCTION