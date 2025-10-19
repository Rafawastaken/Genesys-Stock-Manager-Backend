# app/core/config.py
# Configurações centrais para o aplicativo Genesys API Backend.

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Literal

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)
    # General
    TIMEZONE: str = "Europe/Lisbon"
    # App
    APP_ENV: Literal["dev", "prod"] = "dev"
    APP_PORT:int = 8000
    # Logging
    LOG_LEVEL: str = "DEBUG"
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "genesys"
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    # JWT
    JWT_SECRET: str = "random-jwt"
    JWT_EXPIRE_MIN: int = 120
    JWT_REFRESH_EXPIRE_MIN: int = 43200
    # Prestashop
    PS_AUTH_VALIDATE_URL: str
    PS_GENESYS_KEY: str
    PS_AUTH_VALIDATE_HEADER: str = "X-Genesys-Key"
    PS_USER_AGENT: str = "genesys/2.0"
    PS_AUTH_TIMEOUT_S: int = 10
    PS_AUTH_VERIFY_SSL: str = "true" 
    
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    
    
settings = Settings()