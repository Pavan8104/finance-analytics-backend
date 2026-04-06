from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import exc

from app.core.config import settings
from app.api.api_v1 import api_router
from app.core.database import engine, Base
from app.utils.logger import logger

# Create all database tables (For simplicity in this project instead of Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For real production, change this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Finance Analytics API...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Finance Analytics API...")

@app.get("/", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }
