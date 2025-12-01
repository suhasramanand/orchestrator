"""
API routes for job management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.schemas import JobCreate, JobResponse, JobListResponse
from app.services.job_service import JobService

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    job_create: JobCreate,
    db: Session = Depends(get_db)
):
    """Create a new job."""
    service = JobService(db)
    try:
        job = service.create_job(job_create)
        return JobResponse.from_orm(job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List jobs with pagination and search."""
    service = JobService(db)
    jobs, total = service.list_jobs(page=page, page_size=page_size, search=search)
    
    total_pages = (total + page_size - 1) // page_size
    
    # Convert ORM objects to response models
    job_responses = [JobResponse.from_orm(job) for job in jobs]
    
    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get job by ID."""
    service = JobService(db)
    try:
        job = service.get_job(job_id)
        return JobResponse.from_orm(job)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

