"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.database import Base


class JobStatus(str, enum.Enum):
    """Job status enumeration."""
    PENDING = "PENDING"
    CREATING_TASKS = "CREATING_TASKS"
    ENQUEUED = "ENQUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""
    PENDING = "PENDING"
    ENQUEUED = "ENQUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class Job(Base):
    """Job model representing a distributed computation job."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    job_type = Column(String, nullable=False, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    parameters = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status}, tasks={self.completed_tasks}/{self.total_tasks})>"


class Task(Base):
    """Task model representing a single unit of work."""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    task_index = Column(Integer, nullable=False)  # Order within job
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    parameters = Column(Text)  # JSON string
    result = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, job_id={self.job_id}, status={self.status}, retries={self.retry_count})>"

