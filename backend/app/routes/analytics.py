"""
API routes for analytics and metrics.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview")
async def get_overview(
    db: Session = Depends(get_db)
):
    """Get overview statistics."""
    service = AnalyticsService(db)
    return service.get_overview_stats()


@router.get("/jobs-by-type")
async def get_jobs_by_type(
    db: Session = Depends(get_db)
):
    """Get job counts by type."""
    service = AnalyticsService(db)
    return service.get_jobs_by_type()


@router.get("/jobs-by-status")
async def get_jobs_by_status(
    db: Session = Depends(get_db)
):
    """Get job counts by status."""
    service = AnalyticsService(db)
    return service.get_jobs_by_status()


@router.get("/tasks-by-status")
async def get_tasks_by_status(
    db: Session = Depends(get_db)
):
    """Get task counts by status."""
    service = AnalyticsService(db)
    return service.get_tasks_by_status()


@router.get("/timeline")
async def get_timeline(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get job creation timeline."""
    service = AnalyticsService(db)
    return service.get_jobs_timeline(days=days)


@router.get("/processing-time-stats")
async def get_processing_time_stats(
    db: Session = Depends(get_db)
):
    """Get processing time statistics."""
    service = AnalyticsService(db)
    return service.get_processing_time_stats()


@router.get("/recent-jobs")
async def get_recent_jobs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get recent jobs."""
    service = AnalyticsService(db)
    return service.get_recent_jobs(limit=limit)

