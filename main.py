from fastapi import FastAPI
from backend.app.api.main import api_router
from backend.app.core.config import settings
from contextlib import asynccontextmanager
from backend.app.database.session import engine, AsyncSessionLocal
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Up")
    # Skip database connection test for now
    yield
    print("Shutting Down")
    # Dispose of the engine on shutdown
    await engine.dispose()


app = FastAPI(
    title="Bank Fraud Detection with AI",
    description="Featured Bank API",
    lifespan=lifespan,
)

app.include_router(api_router)