from fastapi import FastAPI
from contextlib import asynccontextmanager


from backend.app.api.main import api_router
from backend.app.core.logging import get_logger
from backend.app.database.session import engine, init_db, check_database_connection

logger = get_logger()




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting application...")

    try:
        # Initialize database with models and connection verification
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")

        logger.info("Application started successfully")

    except Exception as e:
        logger.error(f"Cannot start application - initialization failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        await engine.dispose()
        logger.info("Database engine disposed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info(" Application shutdown completed")


# Create FastAPI app
app = FastAPI(
    title="Bank Fraud Detection with AI",
    description="Featured Bank API",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(api_router)



