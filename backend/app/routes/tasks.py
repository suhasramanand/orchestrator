"""
API routes for task management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import TaskResponse, TaskListResponse, TaskCompleteRequest
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get task by ID."""
    service = TaskService(db)
    try:
        task = service.get_task(task_id)
        return task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}/tasks", response_model=TaskListResponse)
async def get_job_tasks(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get all tasks for a job."""
    service = TaskService(db)
    try:
        tasks = service.get_tasks_by_job(job_id)
        return TaskListResponse(tasks=tasks, total=len(tasks))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    complete_request: TaskCompleteRequest,
    db: Session = Depends(get_db)
):
    """Mark a task as complete (called by worker)."""
    service = TaskService(db)
    try:
        task = service.mark_task_complete(task_id, complete_request)
        return TaskResponse.from_orm(task)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/running", response_model=TaskResponse)
async def mark_task_running(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Mark a task as running (called by worker)."""
    service = TaskService(db)
    try:
        task = service.mark_task_running(task_id)
        return TaskResponse.from_orm(task)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/failed", response_model=TaskResponse)
async def mark_task_failed(
    task_id: str,
    error_request: dict = None,
    db: Session = Depends(get_db)
):
    """Mark a task as failed (called by worker)."""
    service = TaskService(db)
    try:
        # Handle both dict and Pydantic model
        if error_request is None:
            error_request = {}
        error_message = error_request.get("error_message", "Unknown error") if isinstance(error_request, dict) else getattr(error_request, "error_message", "Unknown error")
        task = service.mark_task_failed(task_id, error_message)
        return TaskResponse.from_orm(task)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

