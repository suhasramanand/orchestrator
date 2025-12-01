"""
Kubernetes worker that polls SQS for tasks and processes them.
"""
import os
import time
import json
import signal
import sys
from typing import Optional
import structlog
import requests
from pydantic_settings import BaseSettings
import boto3
from botocore.exceptions import ClientError

logger = structlog.get_logger(__name__)


class WorkerConfig(BaseSettings):
    """Worker configuration."""
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    sqs_queue_url: str = ""
    api_base_url: str = "http://localhost:8000"
    poll_interval_seconds: int = 5
    max_messages_per_poll: int = 10
    wait_time_seconds: int = 20
    worker_id: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class TaskProcessor:
    """Processes individual tasks."""
    
    @staticmethod
    def process_task(task_id: str, job_id: str, task_index: int, parameters: dict) -> dict:
        """
        Process a task - simulates computation work.
        
        In production, this would perform actual work like:
        - Data processing
        - Image transformation
        - ML inference
        - ETL operations
        """
        start_time = time.time()
        
        # Simulate work based on task parameters
        work_duration = parameters.get('work_duration_seconds', 2.0)
        work_type = parameters.get('work_type', 'cpu_bound')
        
        logger.info(
            "Processing task",
            task_id=task_id,
            job_id=job_id,
            work_type=work_type,
            duration=work_duration
        )
        
        if work_type == 'cpu_bound':
            # Simulate CPU-intensive work
            end_time = start_time + work_duration
            while time.time() < end_time:
                # Simple CPU-bound computation
                _ = sum(i * i for i in range(1000))
                time.sleep(0.01)
        elif work_type == 'io_bound':
            # Simulate I/O-bound work
            time.sleep(work_duration)
        elif work_type == 'matrix_multiply':
            # Simulate matrix multiplication
            import numpy as np
            size = parameters.get('matrix_size', 100)
            a = np.random.rand(size, size)
            b = np.random.rand(size, size)
            _ = np.dot(a, b)
            time.sleep(work_duration)
        else:
            # Default: just sleep
            time.sleep(work_duration)
        
        processing_time = time.time() - start_time
        
        # Generate result
        result = {
            "task_id": task_id,
            "job_id": job_id,
            "task_index": task_index,
            "processing_time_seconds": processing_time,
            "work_type": work_type,
            "status": "completed"
        }
        
        logger.info(
            "Task completed",
            task_id=task_id,
            processing_time=processing_time
        )
        
        return result


class SQSWorker:
    """Worker that polls SQS and processes tasks."""
    
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.running = True
        # Determine if using LocalStack or real AWS
        endpoint_url = None
        if config.sqs_queue_url.startswith('http://'):
            # Extract base URL for LocalStack
            parts = config.sqs_queue_url.split('/')
            endpoint_url = '/'.join(parts[:3])  # http://host:port
        
        self.sqs_client = boto3.client(
            'sqs',
            region_name=config.aws_region,
            aws_access_key_id=config.aws_access_key_id or None,
            aws_secret_access_key=config.aws_secret_access_key or None,
            endpoint_url=endpoint_url
        )
        
        # Store queue URL (full URL or queue name)
        self.queue_url = config.sqs_queue_url
        self.processor = TaskProcessor()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(
            "Worker initialized",
            worker_id=config.worker_id,
            queue_url=config.sqs_queue_url,
            api_base_url=config.api_base_url
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal", signal=signum)
        self.running = False
    
    def _receive_tasks(self) -> list:
        """Receive tasks from SQS."""
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=self.config.max_messages_per_poll,
                WaitTimeSeconds=self.config.wait_time_seconds,
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
    
    def _delete_message(self, receipt_handle: str):
        """Delete a message from SQS after processing."""
        try:
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
        except ClientError as e:
            logger.error("Failed to delete message from SQS", error=str(e))
    
    def _mark_task_running(self, task_id: str) -> bool:
        """Mark task as running via API."""
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/v1/tasks/{task_id}/running",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning("Failed to mark task as running", task_id=task_id, error=str(e))
            return False
    
    def _mark_task_complete(self, task_id: str, result: dict, processing_time: float) -> bool:
        """Mark task as complete via API."""
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/v1/tasks/{task_id}/complete",
                json={
                    "result": result,
                    "processing_time_seconds": processing_time
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Failed to mark task as complete", task_id=task_id, error=str(e))
            return False
    
    def _mark_task_failed(self, task_id: str, error_message: str) -> bool:
        """Mark task as failed via API."""
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/v1/tasks/{task_id}/failed",
                json={"error_message": error_message},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Failed to mark task as failed", task_id=task_id, error=str(e))
            return False
    
    def _process_task(self, task: dict):
        """Process a single task."""
        task_id = task['task_id']
        job_id = task['job_id']
        task_index = task['task_index']
        parameters = task['parameters']
        receipt_handle = task['receipt_handle']
        
        try:
            # Mark task as running
            self._mark_task_running(task_id)
            
            # Process the task
            result = self.processor.process_task(task_id, job_id, task_index, parameters)
            processing_time = result['processing_time_seconds']
            
            # Mark task as complete
            if self._mark_task_complete(task_id, result, processing_time):
                # Delete message from SQS only after successful completion
                self._delete_message(receipt_handle)
                logger.info("Task processed successfully", task_id=task_id)
            else:
                logger.error("Failed to mark task complete, message will be retried", task_id=task_id)
                # DO NOT delete message - let it become visible again for retry
                # The message will become visible after visibility timeout
        
        except Exception as e:
            error_msg = str(e)
            logger.error("Task processing failed", task_id=task_id, error=error_msg)
            
            # Mark task as failed
            self._mark_task_failed(task_id, error_msg)
            
            # Only delete message if we successfully marked it as failed
            # Otherwise, let it retry after visibility timeout
            # In production, check retry count and move to DLQ if exceeded
            try:
                self._delete_message(receipt_handle)
            except Exception as delete_error:
                logger.warning("Failed to delete message after failure", task_id=task_id, error=str(delete_error))
    
    def run(self):
        """Main worker loop."""
        logger.info("Worker started", worker_id=self.config.worker_id)
        
        while self.running:
            try:
                # Receive tasks from SQS
                tasks = self._receive_tasks()
                
                if tasks:
                    logger.info("Received tasks", count=len(tasks))
                    
                    # Process each task
                    for task in tasks:
                        if not self.running:
                            break
                        self._process_task(task)
                else:
                    # No tasks, wait before next poll
                    time.sleep(self.config.poll_interval_seconds)
            
            except KeyboardInterrupt:
                logger.info("Worker interrupted")
                break
            except Exception as e:
                logger.error("Error in worker loop", error=str(e))
                time.sleep(self.config.poll_interval_seconds)
        
        logger.info("Worker stopped")


def main():
    """Main entrypoint."""
    # Generate worker ID
    worker_id = os.getenv('WORKER_ID', f"worker-{os.getpid()}")
    
    config = WorkerConfig(
        worker_id=worker_id,
        sqs_queue_url=os.getenv('SQS_QUEUE_URL', ''),
        api_base_url=os.getenv('API_BASE_URL', 'http://localhost:8000'),
        aws_region=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', ''),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', ''),
    )
    
    if not config.sqs_queue_url:
        logger.error("SQS_QUEUE_URL environment variable is required")
        sys.exit(1)
    
    worker = SQSWorker(config)
    worker.run()


if __name__ == "__main__":
    main()

