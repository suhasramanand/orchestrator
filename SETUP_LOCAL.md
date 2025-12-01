# Local Development Setup Guide

This guide will help you set up and test the Job Orchestration Platform locally.

## Prerequisites

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)
4. **Kubernetes cluster** (one of):
   - [kind](https://kind.sigs.k8s.io/) - Recommended for local testing
   - [minikube](https://minikube.sigs.k8s.io/)
   - Docker Desktop with Kubernetes enabled

## Step 1: Start Local Services

### Start Postgres Database

```bash
docker-compose up -d postgres
```

Verify it's running:
```bash
docker ps | grep postgres
```

## Step 2: Setup Backend

### Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the `backend` directory:

```bash
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobdb
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
EOF
```

### Run Database Migrations

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobdb
python -m alembic upgrade head
```

### Start Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

Test it:
```bash
curl http://localhost:8000/health
```

## Step 3: Setup Frontend

### Install Dependencies

```bash
cd frontend
npm install
```

### Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Step 4: Setup Local SQS (Optional - for testing without AWS)

For local testing without AWS, you can use [LocalStack](https://localstack.cloud/):

```bash
# Install LocalStack
pip install localstack

# Start LocalStack
localstack start -d

# Create SQS queue
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name tasks
```

Get the queue URL:
```bash
aws --endpoint-url=http://localhost:4566 sqs get-queue-url --queue-name tasks
```

## Step 5: Setup Worker

### Option A: Run Worker Locally (Without Kubernetes)

Create a `.env` file in the `worker` directory:

```bash
cd worker
cat > .env << EOF
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
SQS_QUEUE_URL=http://localhost:4566/000000000000/tasks  # LocalStack URL
API_BASE_URL=http://localhost:8000
WORKER_ID=local-worker-1
EOF
```

Install dependencies and run:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python worker.py
```

### Option B: Deploy Worker to Kubernetes

#### 1. Build Worker Docker Image

```bash
cd worker
docker build -t job-worker:latest .
```

#### 2. Load Image into Kubernetes (if using kind)

```bash
kind load docker-image job-worker:latest
```

#### 3. Create Kubernetes Secrets

```bash
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id=test \
  --from-literal=secret-access-key=test
```

#### 4. Update ConfigMap with SQS Queue URL

Edit `infra/k8s/configmap.yaml` and set the SQS queue URL, or create it:

```bash
kubectl create configmap job-worker-config \
  --from-literal=AWS_REGION=us-east-1 \
  --from-literal=API_BASE_URL=http://backend-service:8000 \
  --from-literal=SQS_QUEUE_URL=http://localhost:4566/000000000000/tasks
```

#### 5. Deploy Worker

```bash
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/configmap.yaml
```

#### 6. Check Worker Status

```bash
kubectl get pods -l app=job-worker
kubectl logs -f deployment/job-worker
```

## Step 6: Test the System

### 1. Create a Job via API

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "compute",
    "num_tasks": 5,
    "parameters": {
      "work_type": "cpu_bound",
      "work_duration_seconds": 2.0
    }
  }'
```

### 2. Check Job Status

```bash
# Get the job_id from the previous response
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### 3. View Jobs in Frontend

Open `http://localhost:3000` in your browser and:
- Click "Create Job" to submit a new job
- View the job list to see all jobs
- Click on a job to see detailed task progress

### 4. Monitor Worker Logs

If running locally:
```bash
# Worker logs will show task processing
```

If running in Kubernetes:
```bash
kubectl logs -f deployment/job-worker
```

## Troubleshooting

### Backend Issues

1. **Database connection error**:
   - Ensure Postgres is running: `docker ps | grep postgres`
   - Check DATABASE_URL in `.env`

2. **Migration errors**:
   - Drop and recreate database:
     ```bash
     docker-compose down -v
     docker-compose up -d postgres
     python -m alembic upgrade head
     ```

### Frontend Issues

1. **API connection errors**:
   - Ensure backend is running on port 8000
   - Check CORS settings in backend

### Worker Issues

1. **SQS connection errors**:
   - Verify SQS_QUEUE_URL is correct
   - If using LocalStack, ensure it's running: `localstack status`

2. **API connection errors**:
   - Verify API_BASE_URL is correct
   - Ensure backend is accessible from worker

### Kubernetes Issues

1. **Image pull errors**:
   - If using kind, ensure image is loaded: `kind load docker-image job-worker:latest`
   - Check image name in deployment.yaml

2. **Pod not starting**:
   - Check pod logs: `kubectl logs <pod-name>`
   - Verify secrets and configmaps exist

## Next Steps

Once local testing works:

1. **Deploy to AWS**:
   - Set up AWS credentials
   - Deploy Terraform infrastructure
   - Update environment variables

2. **Deploy to EKS**:
   - Create EKS cluster
   - Deploy worker to EKS
   - Configure networking

3. **Add Monitoring**:
   - Set up CloudWatch dashboards
   - Add structured logging
   - Configure alerts

## Useful Commands

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev

# Worker (local)
cd worker
python worker.py

# Kubernetes
kubectl get pods
kubectl logs -f deployment/job-worker
kubectl describe pod <pod-name>

# Database
docker-compose exec postgres psql -U postgres -d jobdb
```

