"""
Business logic for task management.
"""
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.db.models import Task, TaskStatus, Job
from app.models.schemas import TaskCompleteRequest
from app.services.job_service import JobService

logger = structlog.get_logger(__name__)


class TaskService:
    """Service for task operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.job_service = JobService(db)
    
    def get_task(self, task_id: str) -> Task:
        """Get task by ID."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        return task
    
    def get_tasks_by_job(self, job_id: str) -> list[Task]:
        """Get all tasks for a job."""
        tasks = self.db.query(Task).filter(Task.job_id == job_id).order_by(Task.task_index).all()
        return tasks
    
    def mark_task_complete(
        self,
        task_id: str,
        complete_request: TaskCompleteRequest
    ) -> Task:
        """Mark a task as completed (called by worker)."""
        task = self.get_task(task_id)
        
        if task.status == TaskStatus.COMPLETED:
            logger.warning("Task already completed", task_id=task_id)
            return task
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result = str(complete_request.result) if complete_request.result else None
        task.processing_time_seconds = complete_request.processing_time_seconds
        
        if task.started_at:
            # Calculate processing time if not provided
            if not task.processing_time_seconds:
                delta = task.completed_at - task.started_at
                task.processing_time_seconds = delta.total_seconds()
        
        self.db.commit()
        logger.info("Task completed", task_id=task_id, job_id=task.job_id)
        
        # Update job completion stats
        self.job_service.update_task_completion(task.job_id)
        
        return task
    
    def mark_task_failed(self, task_id: str, error_message: str):
        """Mark a task as failed."""
        task = self.get_task(task_id)
        
        task.retry_count += 1
        
        if task.retry_count >= task.max_retries:
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            task.completed_at = datetime.utcnow()
            logger.error(
                "Task failed after max retries",
                task_id=task_id,
                retries=task.retry_count
            )
        else:
            task.status = TaskStatus.RETRYING
            logger.warning(
                "Task retrying",
                task_id=task_id,
                retry_count=task.retry_count,
                max_retries=task.max_retries
            )
        
        self.db.commit()
        
        # Update job stats if task is permanently failed
        if task.status == TaskStatus.FAILED:
            self.job_service.update_task_completion(task.job_id)
        
        return task
    
    def mark_task_running(self, task_id: str) -> Task:
        """Mark a task as running."""
        task = self.get_task(task_id)
        
        if task.status == TaskStatus.PENDING or task.status == TaskStatus.ENQUEUED:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            self.db.commit()
            logger.info("Task started", task_id=task_id, job_id=task.job_id)
        
        return task

