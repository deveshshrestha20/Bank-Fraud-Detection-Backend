from fastapi import FastAPI
from backend.app.api.main import api_router
from backend.app.core.config import settings
app = FastAPI(
    title="Bank Fraud Detection with AI",
    description="Featured Bank API ",
)

app.include_router(api_router)

