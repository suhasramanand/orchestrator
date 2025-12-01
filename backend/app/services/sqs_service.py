"""
Service for AWS SQS integration.
"""
import json
import boto3
from botocore.exceptions import ClientError
import structlog
from app.utils.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class SQSService:
    """Service for SQS operations."""
    
    def __init__(self):
        # Determine endpoint URL for LocalStack
        endpoint_url = None
        queue_url = settings.sqs_queue_url or "http://localhost:4566/000000000000/tasks"
        
        if queue_url.startswith('http://'):
            # Extract base URL for LocalStack (e.g., http://localhost:4566)
            parts = queue_url.split('/')
            endpoint_url = '/'.join(parts[:3])  # http://host:port
        
        self.client = boto3.client(
            'sqs',
            region_name=settings.aws_region or 'us-east-1',
            aws_access_key_id=settings.aws_access_key_id or 'test',
            aws_secret_access_key=settings.aws_secret_access_key or 'test',
            endpoint_url=endpoint_url
        )
        self.queue_url = queue_url
    
    def send_task(self, task_id: str, job_id: str, task_index: int, parameters: dict = None):
        """Send a task message to SQS."""
        message = {
            "task_id": task_id,
            "job_id": job_id,
            "task_index": task_index,
            "parameters": parameters or {}
        }
        
        try:
            response = self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message)
            )
            logger.info("Task sent to SQS", task_id=task_id, message_id=response.get('MessageId'))
            return response
        except ClientError as e:
            logger.error("Failed to send task to SQS", error=str(e))
            raise
    
    def send_message(self, message_body: dict):
        """Send a message to SQS (alias for send_task with dict)."""
        return self.send_task(
            task_id=message_body['task_id'],
            job_id=message_body['job_id'],
            task_index=message_body['task_index'],
            parameters=message_body.get('parameters', {})
        )
    
    def receive_tasks(self, max_messages: int = 10, wait_time_seconds: int = 20):
        """Receive tasks from SQS queue."""
        try:
            response = self.client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            tasks = []
            
            for msg in messages:
                try:
                    body = json.loads(msg['Body'])
                    tasks.append({
                        'receipt_handle': msg['ReceiptHandle'],
                        'message_id': msg['MessageId'],
                        'task_id': body['task_id'],
                        'job_id': body['job_id'],
                        'task_index': body['task_index'],
                        'parameters': body.get('parameters', {})
                    })
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error("Failed to parse SQS message", error=str(e))
                    continue
            
            return tasks
        except ClientError as e:
            logger.error("Failed to receive messages from SQS", error=str(e))
            return []
    
    def delete_message(self, receipt_handle: str):
        """Delete a message from SQS after processing."""
        try:
            self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.debug("Message deleted from SQS", receipt_handle=receipt_handle[:20])
        except ClientError as e:
            logger.error("Failed to delete message from SQS", error=str(e))
            raise

