"""
Pydantic schemas for API request/response models.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any
from datetime import datetime
from app.db.models import JobStatus, TaskStatus
import json
import ast


# Job Schemas
class JobCreate(BaseModel):
    """Schema for creating a new job."""
    job_type: str = Field(..., description="Type of job (e.g., 'compute', 'data_processing')")
    num_tasks: int = Field(..., ge=1, le=10000, description="Number of tasks to create")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Job-specific parameters")


class JobResponse(BaseModel):
    """Schema for job response."""
    id: str
    job_type: str
    status: JobStatus
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    parameters: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to parse parameters string to dict."""
        data = {
            "id": obj.id,
            "job_type": obj.job_type,
            "status": obj.status.value if hasattr(obj.status, 'value') else obj.status,
            "total_tasks": obj.total_tasks,
            "completed_tasks": obj.completed_tasks,
            "failed_tasks": obj.failed_tasks,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "started_at": obj.started_at,
            "completed_at": obj.completed_at,
            "error_message": obj.error_message,
        }
        
        # Parse parameters string to dict
        if obj.parameters:
            try:
                import ast
                data["parameters"] = ast.literal_eval(obj.parameters)
            except:
                data["parameters"] = None
        
        return cls(**data)
    
    class Config:
        from_attributes = True
        use_enum_values = True


class JobListResponse(BaseModel):
    """Schema for paginated job list."""
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Task Schemas
class TaskResponse(BaseModel):
    """Schema for task response."""
    id: str
    job_id: str
    status: TaskStatus
    task_index: int
    retry_count: int
    max_retries: int
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    
    @model_validator(mode='before')
    @classmethod
    def parse_dict_fields(cls, data: Any) -> Any:
        """Parse parameters and result strings to dicts."""
        # Handle ORM objects (from SQLAlchemy)
        if hasattr(data, '__dict__') and not isinstance(data, dict):
            # Convert ORM object to dict
            data_dict = {}
            for key in ['id', 'job_id', 'status', 'task_index', 'retry_count', 'max_retries',
                       'parameters', 'result', 'error_message', 'created_at', 'updated_at',
                       'started_at', 'completed_at', 'processing_time_seconds']:
                if hasattr(data, key):
                    value = getattr(data, key)
                    # Handle enum
                    if key == 'status' and hasattr(value, 'value'):
                        data_dict[key] = value.value
                    else:
                        data_dict[key] = value
            data = data_dict
        
        if isinstance(data, dict):
            # Parse parameters string to dict
            if 'parameters' in data and isinstance(data['parameters'], str):
                try:
                    data['parameters'] = ast.literal_eval(data['parameters'])
                except:
                    try:
                        data['parameters'] = json.loads(data['parameters'])
                    except:
                        data['parameters'] = None
            
            # Parse result string to dict
            if 'result' in data and isinstance(data['result'], str):
                try:
                    data['result'] = ast.literal_eval(data['result'])
                except:
                    try:
                        data['result'] = json.loads(data['result'])
                    except:
                        data['result'] = None
        
        return data
    
    class Config:
        from_attributes = True


class TaskCompleteRequest(BaseModel):
    """Schema for task completion request from worker."""
    result: Optional[Dict[str, Any]] = None
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None


class TaskListResponse(BaseModel):
    """Schema for task list response."""
    tasks: list[TaskResponse]
    total: int

