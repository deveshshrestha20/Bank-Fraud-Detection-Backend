from fastapi import FastAPI
from backend.app.api.main import api_router
from backend.app.core.config import settings
from contextlib import asynccontextmanager

from backend.app.database.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Up")
    db = SessionLocal()
    yield
    print("Shutting Down")
app = FastAPI(
    title="Bank Fraud Detection with AI",
    description="Featured Bank API ",
    lifespan=lifespan,
)

app.include_router(api_router)

