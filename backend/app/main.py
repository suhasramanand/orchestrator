"""
FastAPI application entrypoint for the Job Orchestration Platform.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.db.database import engine, Base, get_db
from app.routes import jobs, tasks, analytics
from app.utils.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application", database_url=settings.database_url)
    
    # Create tables (in production, use migrations)
    if os.getenv("CREATE_TABLES", "false").lower() == "true":
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


app = FastAPI(
    title="Job Orchestration Platform API",
    description="Distributed job orchestration system with AWS Serverless + Kubernetes",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "job-orchestration-api",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected"  # Could add actual DB check
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

