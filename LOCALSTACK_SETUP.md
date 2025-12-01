# LocalStack Setup Guide

## Overview
LocalStack provides local AWS service emulation for development and testing. This guide covers setting up LocalStack with SQS for the distributed job orchestration platform.

## Quick Start

### 1. Start LocalStack
```bash
docker-compose -f docker-compose.localstack.yml up -d
```

### 2. Wait for LocalStack to be ready
```bash
curl http://localhost:4566/_localstack/health
```

### 3. Create SQS Queue
```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name tasks \
    --region us-east-1
```

### 4. Get Queue URL
```bash
aws --endpoint-url=http://localhost:4566 sqs get-queue-url \
    --queue-name tasks \
    --region us-east-1 \
    --query 'QueueUrl' \
    --output text
```

## Kubernetes Integration

### Option 1: Expose LocalStack as Kubernetes Service

1. Get LocalStack IP:
```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' localstack
```

2. Create Kubernetes Service and Endpoints:
```bash
kubectl apply -f infra/k8s/localstack-endpoints.yaml
```

3. Update worker deployment to use `localstack:4566` as the queue URL.

### Option 2: Connect LocalStack to Kind Network

```bash
docker network connect kind localstack
```

Then use the LocalStack container IP or service name in your worker configuration.

## Configuration

### Environment Variables
- `AWS_ACCESS_KEY_ID=test` (dummy credentials for LocalStack)
- `AWS_SECRET_ACCESS_KEY=test`
- `AWS_ENDPOINT_URL=http://localhost:4566` (for AWS CLI)
- `SQS_QUEUE_URL=http://localhost:4566/000000000000/tasks` (from host)
- `SQS_QUEUE_URL=http://localstack:4566/000000000000/tasks` (from K8s pods)

### Queue URL Format
- From host machine: `http://localhost:4566/000000000000/tasks`
- From Kubernetes pods: `http://localstack:4566/000000000000/tasks` (if service is created)
- Direct IP: `http://<LOCALSTACK_IP>:4566/000000000000/tasks`

## Testing

### Send a test message
```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

aws --endpoint-url=http://localhost:4566 sqs send-message \
    --queue-url http://localhost:4566/000000000000/tasks \
    --message-body '{"task_id": "test-1", "job_id": "job-1", "task_index": 0, "parameters": {}}' \
    --region us-east-1
```

### Receive messages
```bash
aws --endpoint-url=http://localhost:4566 sqs receive-message \
    --queue-url http://localhost:4566/000000000000/tasks \
    --region us-east-1
```

## Troubleshooting

### Workers can't connect to LocalStack
1. Verify LocalStack is running: `docker ps | grep localstack`
2. Check LocalStack health: `curl http://localhost:4566/_localstack/health`
3. For Kubernetes pods, ensure:
   - LocalStack service is created
   - Queue URL uses service name or correct IP
   - Network connectivity is established

### Queue not found
- Ensure queue is created before workers start
- Verify queue name matches configuration
- Check AWS credentials are set (even dummy ones for LocalStack)

## Files
- `docker-compose.localstack.yml` - LocalStack Docker Compose configuration
- `setup_localstack.sh` - Automated setup script
- `infra/k8s/localstack-endpoints.yaml` - Kubernetes service/endpoints for LocalStack

## Next Steps
1. Update worker deployment with correct queue URL
2. Test end-to-end: Create job → Tasks enqueued → Workers process
3. Monitor worker logs: `kubectl logs -f deployment/job-worker`

