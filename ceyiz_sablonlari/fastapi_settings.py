# {{PROJE_AD}} — Ayarlar

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "{{PROJE_AD}}"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = {{PROJE_PORT}}

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///data/{{PROJE_KLASOR}}.db"

    # Auth
    SECRET_KEY: str = "emare-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()
