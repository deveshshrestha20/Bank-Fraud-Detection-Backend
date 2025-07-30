from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from dotenv import load_dotenv
from backend.app.core.config import settings
from typing import AsyncGenerator

load_dotenv()

# Use async database URL (postgresql+asyncpg://)
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()