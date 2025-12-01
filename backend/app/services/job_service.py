"""
Business logic for job management.
"""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import structlog

from app.db.models import Job, JobStatus, Task, TaskStatus
from app.models.schemas import JobCreate
from app.services.step_functions_service import StepFunctionsService
from app.utils.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class JobService:
    """Service for job operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.step_functions = StepFunctionsService()
    
    def create_job(self, job_create: JobCreate) -> Job:
        """Create a new job and initiate Step Functions workflow."""
        job_id = str(uuid.uuid4())
        
        job = Job(
            id=job_id,
            job_type=job_create.job_type,
            status=JobStatus.PENDING,
            total_tasks=job_create.num_tasks,
            completed_tasks=0,
            failed_tasks=0,
            parameters=str(job_create.parameters) if job_create.parameters else None,
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        logger.info("Job created", job_id=job_id, num_tasks=job_create.num_tasks)
        
        # Start Step Functions workflow (if configured)
        if settings.step_functions_arn:
            try:
                self.step_functions.start_execution(job_id, job_create.num_tasks, job_create.parameters)
                job.status = JobStatus.CREATING_TASKS
                self.db.commit()
            except Exception as e:
                logger.error("Failed to start Step Functions", job_id=job_id, error=str(e))
                # Continue anyway - tasks can be created manually
        else:
            # Local development: create tasks directly
            self._create_tasks_local(job, job_create.num_tasks, job_create.parameters)
        
        return job
    
    def _create_tasks_local(self, job: Job, num_tasks: int, parameters: dict):
        """Create tasks locally (for development without Step Functions)."""
        from app.services.sqs_service import SQSService
        
        tasks = []
        for i in range(num_tasks):
            task_id = f"{job.id}-task-{i}"
            task = Task(
                id=task_id,
                job_id=job.id,
                status=TaskStatus.ENQUEUED,
                task_index=i,
                parameters=str(parameters) if parameters else None,
            )
            tasks.append(task)
        
        self.db.add_all(tasks)
        job.status = JobStatus.ENQUEUED
        self.db.commit()
        
        logger.info("Tasks created locally", job_id=job.id, num_tasks=num_tasks)
        
        # Enqueue tasks to SQS
        sqs_service = SQSService()
        for task in tasks:
            try:
                message_body = {
                    "task_id": task.id,
                    "job_id": task.job_id,
                    "task_index": task.task_index,
                    "parameters": parameters or {}
                }
                sqs_service.send_message(message_body)
                logger.info("Task enqueued to SQS", task_id=task.id)
            except Exception as e:
                logger.error("Failed to enqueue task to SQS", task_id=task.id, error=str(e))
    
    def get_job(self, job_id: str) -> Job:
        """Get job by ID."""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return job
    
    def list_jobs(self, page: int = 1, page_size: int = 20, search: str = None) -> tuple[list[Job], int]:
        """List jobs with pagination and search."""
        offset = (page - 1) * page_size
        query = self.db.query(Job)
        
        # Apply search filter if provided
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Job.id.ilike(search_term),
                    Job.job_type.ilike(search_term)
                )
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering, pagination
        jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(page_size).all()
        
        return jobs, total
    
    def update_job_status(self, job_id: str, status: JobStatus, error_message: str = None):
        """Update job status."""
        job = self.get_job(job_id)
        job.status = status
        job.updated_at = datetime.utcnow()
        
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        
        if error_message:
            job.error_message = error_message
        
        self.db.commit()
        logger.info("Job status updated", job_id=job_id, status=status.value)
    
    def update_task_completion(self, job_id: str):
        """Update job completion stats based on task statuses."""
        job = self.get_job(job_id)
        
        completed = self.db.query(func.count(Task.id)).filter(
            Task.job_id == job_id,
            Task.status == TaskStatus.COMPLETED
        ).scalar()
        
        failed = self.db.query(func.count(Task.id)).filter(
            Task.job_id == job_id,
            Task.status == TaskStatus.FAILED
        ).scalar()
        
        job.completed_tasks = completed or 0
        job.failed_tasks = failed or 0
        
        # Update job status based on task completion
        if job.completed_tasks + job.failed_tasks == job.total_tasks:
            if job.failed_tasks == 0:
                job.status = JobStatus.COMPLETED
            else:
                # Job partially failed - could be configurable
                job.status = JobStatus.COMPLETED  # Or FAILED if strict
            job.completed_at = datetime.utcnow()
        elif job.completed_tasks + job.failed_tasks > 0:
            job.status = JobStatus.RUNNING
            if not job.started_at:
                job.started_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(
            "Job stats updated",
            job_id=job_id,
            completed=job.completed_tasks,
            failed=job.failed_tasks,
            total=job.total_tasks
        )

