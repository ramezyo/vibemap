from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, StaticPool
from config import get_settings

settings = get_settings()

# Check if using SQLite (for testing/demo)
IS_SQLITE = settings.database_url.startswith("sqlite")

if IS_SQLITE:
    # SQLite async engine for testing
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL engine for production
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        poolclass=NullPool,
    )

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database sessions."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
