"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/jobdb"
    
    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    
    # SQS
    sqs_queue_url: str = ""
    sqs_dlq_url: str = ""
    
    # Step Functions
    step_functions_arn: str = ""
    
    # API
    api_base_url: str = "http://localhost:8000"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Job settings
    max_task_retries: int = 3
    task_timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = False


_settings: Settings = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

