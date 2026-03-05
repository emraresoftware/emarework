"""
Veritabanı bağlantısı ve oturum yönetimi
Production-ready: async SQLAlchemy + connection pooling
"""
from sqlalchemy import text  # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker  # type: ignore
from sqlalchemy.orm import DeclarativeBase  # type: ignore
from src.config import settings
import structlog  # type: ignore

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """SQLAlchemy deklaratif taban sınıfı. Tüm modeller bu sınıftan türer."""
    pass


# Database engine - connection pooling ile
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Connection health check
    pool_recycle=3600,    # 1 saat sonra connection yenile
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    """
    Dependency for FastAPI - DB session
    
    Usage:
        @app.get("/")
        async def handler(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Veritabanı başlatma - tabloları oluştur ve extension'ları etkinleştir
    """
    logger.info("db_init_start")
    
    async with engine.begin() as conn:
        # Tabloları oluştur
        await conn.run_sync(Base.metadata.create_all)
        logger.info("db_tables_created")
        
        # PostgreSQL extensions (opsiyonel)
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            logger.info("db_extension_enabled", extension="pg_trgm")
        except Exception as e:
            logger.warning("db_extension_failed", extension="pg_trgm", error=str(e))
        
        # Partitioning için custom SQL (opsiyonel)
        # Her seviye için ayrı partition (0-3, 4-6, 7-10)
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_nodes_level ON nodes(level);
                CREATE INDEX IF NOT EXISTS idx_nodes_address ON nodes(address);
                CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
                CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_address);
            """))
            logger.info("db_indexes_created")
        except Exception as e:
            logger.warning("db_indexes_failed", error=str(e))
    
    logger.info("db_init_complete")


async def close_db():
    """Veritabanı bağlantılarını kapat"""
    global engine
    await engine.dispose()
    logger.info("db_connections_closed")
