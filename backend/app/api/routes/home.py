from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.database.session import get_db, check_database_connection
from backend.app.core.logging import get_logger

logger = get_logger()
router = APIRouter()

@router.get("/")
async def home():
    """Welcome endpoint for the Bank API"""
    logger.info("Home endpoint accessed")
    return {"message": "Welcome to the Bank API !!!!"}

@router.get("/status")
async def home_status():
    """Status endpoint for the home module"""
    return {"module": "home", "status": "active", "version": "1.0.0"}

@router.get("/test-db")
async def test_db_connection(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        return {"status": "Database connected!", "result": result.scalar()}
    except Exception as e:
        return {"error": str(e)}

@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    db_healthy = await check_database_connection()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "service": "Bank Fraud Detection API"
    }