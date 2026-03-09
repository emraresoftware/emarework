"""
Hive Coordinator - Yapılandırma
Production-ready settings with Pydantic
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Uygulama ayarları - .env dosyasından yüklenir"""
    
    # Genel
    app_name: str = "Hive Coordinator"
    version: str = "1.0.0"
    debug: bool = False
    
    # Sunucu
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Database (PostgreSQL)
    database_url: str = "postgresql+asyncpg://hive:hive_secret@localhost:5432/hive_coordinator"
    
    # Redis (Cache + Queue)
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300  # 5 dakika
    
    # Celery (Task Queue)
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_worker_concurrency: int = 10
    
    # Hiyerarşi
    hierarchy_depth: int = 10
    branch_factor: int = 10
    
    # Performans
    aggregation_interval_sec: int = 30
    heartbeat_timeout_sec: int = 300
    max_cascade_depth: int = 10
    batch_register_max_depth: int = 5
    
    # Yük Dengeleme
    overload_threshold_pct: float = 90.0
    rebalance_trigger_pct: float = 30.0
    min_efficiency_threshold: float = 0.5
    
    # Mesajlaşma
    default_message_ttl_sec: int = 3600
    max_broadcast_depth: int = 10
    message_retry_count: int = 3
    message_retry_delay_sec: int = 5
    
    # Güvenlik
    secret_key: str = "change-this-in-production"
    api_key: Optional[str] = None
    allowed_origins: list[str] = ["*"]
    
    # Loglama
    log_level: str = "INFO"
    log_format: str = "json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Uygulama ayarlarını döner, önbelleğe alınmış singleton"""
    return Settings()


# Global settings instance
settings = get_settings()
