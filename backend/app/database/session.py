import asyncio
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger()


def load_models():
    """Load all database models"""
    try:
        # Import all your models here to ensure they are registered with SQLModel
        # Example:
        # from backend.app.models.user import User
        # from backend.app.models.transaction import Transaction
        # from backend.app.models.fraud_detection import FraudDetection

        logger.info("All models imported successfully")
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        raise


# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False,  # Set to True for SQL query logging in development
)

# Create async session maker
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session
    Usage: session: AsyncSession = Depends(get_session)
    """
    session = async_session()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if session:
            try:
                await session.rollback()
                logger.info("Successfully rolled back session after error")
            except Exception as rollback_error:
                logger.error(f"Error during session rollback: {rollback_error}")
        raise
    finally:
        if session:
            try:
                await session.close()
                logger.debug("Database session closed successfully")
            except Exception as close_error:
                logger.error(f"Error closing database session: {close_error}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Alternative dependency function name (commonly used)
    Usage: db: AsyncSession = Depends(get_db)
    """
    async for session in get_session():
        yield session


async def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            await session.commit()
        logger.info("Database connection check successful")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def init_db() -> None:
    """Initialize database with models and connection verification"""
    try:
        # Load all models
        load_models()
        logger.info("Models loaded successfully")

        # Verify database connection with retries
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                logger.info("Database connection verified successfully")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to verify database connection after {max_retries} attempts: {e}"
                    )
                    raise
                logger.warning(
                    f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                await asyncio.sleep(retry_delay * (attempt + 1))

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_db() -> None:
    """Close database connections and dispose engine"""
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


# Health check function for monitoring
async def database_health_check() -> dict:
    """Comprehensive database health check"""
    try:
        start_time = asyncio.get_event_loop().time()

        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            await session.commit()

        end_time = asyncio.get_event_loop().time()
        response_time = round((end_time - start_time) * 1000, 2)  # ms

        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "connection_pool": {
                "size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": None,
        }