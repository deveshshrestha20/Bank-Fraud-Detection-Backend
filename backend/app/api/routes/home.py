from fastapi import APIRouter
from backend.app.core.logging import get_logger

logger = get_logger()
router = APIRouter()

@router.get("/")
def home():
    logger.info("Home Page Accessed")
    logger.debug("Home Page Accessed")
    logger.error("Home Page Accessed")
    logger.warning("Home Page Accessed")
    logger.critical("Home Page Accessed")
    return {"message": "Welcome to the Bank API !!!!"}


