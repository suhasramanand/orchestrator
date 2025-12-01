"""
Service for AWS Step Functions integration.
"""
import json
import boto3
from botocore.exceptions import ClientError
import structlog
from app.utils.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class StepFunctionsService:
    """Service for Step Functions operations."""
    
    def __init__(self):
        if settings.step_functions_arn:
            self.client = boto3.client(
                'stepfunctions',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id or None,
                aws_secret_access_key=settings.aws_secret_access_key or None,
            )
        else:
            self.client = None
            logger.info("Step Functions not configured, using local mode")
    
    def start_execution(self, job_id: str, num_tasks: int, parameters: dict = None):
        """Start a Step Functions execution for a job."""
        if not self.client:
            logger.warning("Step Functions client not available")
            return
        
        input_data = {
            "job_id": job_id,
            "num_tasks": num_tasks,
            "parameters": parameters or {}
        }
        
        try:
            response = self.client.start_execution(
                stateMachineArn=settings.step_functions_arn,
                name=f"job-{job_id}",
                input=json.dumps(input_data)
            )
            logger.info(
                "Step Functions execution started",
                job_id=job_id,
                execution_arn=response.get('executionArn')
            )
            return response
        except ClientError as e:
            logger.error("Failed to start Step Functions execution", error=str(e))
            raise

