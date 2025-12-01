# Kubernetes Local Setup Guide

## Prerequisites

1. **Start Docker Desktop**
   - Open Docker Desktop application
   - Wait for it to fully start (whale icon in menu bar)
   - Verify: `docker info` should work

2. **Install kind** (if not installed)
   ```bash
   brew install kind
   ```

## Step-by-Step Setup

### Step 1: Create Kubernetes Cluster

```bash
cd distributed-job-orchestration
./setup_k8s.sh
```

Or manually:
```bash
kind create cluster --name job-orchestration --wait 5m
```

### Step 2: Build and Deploy Worker

```bash
./deploy_to_k8s.sh
```

Or manually:
```bash
# Build image
cd worker
docker build -t job-worker:latest .

# Load into kind
kind load docker-image job-worker:latest --name job-orchestration

# Deploy
cd ../infra/k8s
kubectl apply -f configmap.yaml
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id=test \
  --from-literal=secret-access-key=test

# Update API URL for local backend
kubectl patch configmap job-worker-config --type merge \
  -p '{"data":{"API_BASE_URL":"http://host.docker.internal:8000"}}'

# Deploy worker
kubectl apply -f deployment.yaml
```

### Step 3: Verify Deployment

```bash
# Check pods
kubectl get pods -l app=job-worker

# View logs
kubectl logs -f deployment/job-worker

# Check deployment status
kubectl get deployments
kubectl describe deployment job-worker
```

## Testing

1. **Create a job via API**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/jobs \
     -H "Content-Type: application/json" \
     -d '{"job_type": "compute", "num_tasks": 5, "parameters": {"work_type": "cpu_bound", "work_duration_seconds": 1.0}}'
   ```

2. **Watch worker logs**:
   ```bash
   kubectl logs -f deployment/job-worker
   ```

3. **Check job status**:
   ```bash
   curl http://localhost:8000/api/v1/jobs
   ```

## Troubleshooting

### Docker not running
- Start Docker Desktop
- Wait for it to fully initialize
- Run `docker info` to verify

### Image pull errors
- Ensure image is loaded: `kind load docker-image job-worker:latest --name job-orchestration`
- Check image exists: `docker images | grep job-worker`

### Pod not starting
- Check pod status: `kubectl describe pod <pod-name>`
- View events: `kubectl get events --sort-by='.lastTimestamp'`
- Check logs: `kubectl logs <pod-name>`

### Worker can't reach backend
- Backend must be running on localhost:8000
- Use `host.docker.internal:8000` in ConfigMap (already set)
- Verify backend is accessible: `curl http://localhost:8000/health`

### SQS connection issues
- For local testing without SQS, workers will fail to poll
- You can mock SQS or use LocalStack
- Or comment out SQS polling in worker for testing

## Cleanup

```bash
# Delete deployment
kubectl delete -f infra/k8s/deployment.yaml

# Delete cluster
kind delete cluster --name job-orchestration
```
