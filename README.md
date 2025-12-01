# Distributed Job Orchestration Platform

A production-ready distributed job orchestration system that combines AWS Serverless services (Step Functions, SQS, Lambda) with Kubernetes for scalable compute. Users submit jobs via REST API, which are automatically broken into parallel tasks, orchestrated through AWS Step Functions, queued in SQS, and processed by Kubernetes workers.

## Table of Contents

- [What This Project Is About](#what-this-project-is-about)
- [Job Examples & Scenarios](#job-examples--scenarios)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Detailed Setup Guide](#detailed-setup-guide)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [LocalStack Setup](#localstack-setup)
  - [Kubernetes Setup](#kubernetes-setup)
  - [Worker Deployment](#worker-deployment)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Development Notes](#development-notes)
- [Resume Highlights](#resume-highlights)

## What This Project Is About

This is a **distributed job orchestration platform** that demonstrates how to build a scalable system for processing large workloads by breaking them into smaller, parallel tasks. Think of it like a job queue system where:

1. **You submit a job** (e.g., "process 1000 images" or "run ML inference on a dataset")
2. **The system splits it** into smaller tasks (e.g., 1000 tasks, one per image)
3. **Tasks are queued** in AWS SQS (or LocalStack for local dev)
4. **Kubernetes workers** pull tasks from the queue and process them in parallel
5. **Progress is tracked** in real-time through a web dashboard

### Real-World Use Cases

- **Data Processing**: ETL pipelines, batch data transformations
- **ML Inference**: Running predictions on large datasets
- **Image/Video Processing**: Thumbnail generation, format conversion
- **Report Generation**: Creating reports from large datasets
- **Scientific Computing**: Parallel simulations, matrix operations

## Job Examples & Scenarios

### Example 1: Image Processing Pipeline

**Scenario**: A photo-sharing app needs to generate thumbnails for 10,000 uploaded images.

**Job Submission**:
```json
POST /api/v1/jobs
{
  "job_type": "data_processing",
  "total_tasks": 10000,
  "parameters": {
    "work_type": "io_bound",
    "duration_seconds": 2,
    "description": "Generate thumbnails for uploaded images"
  }
}
```

**What Happens**:
1. System creates a job with 10,000 tasks
2. Each task represents processing one image
3. Tasks are enqueued to SQS
4. Kubernetes workers (scaled to 50 pods) pull tasks in parallel
5. Each worker downloads image, generates thumbnails, uploads results
6. Dashboard shows real-time progress
7. Job completes in ~4 minutes (vs. 5+ hours sequentially)

### Example 2: ML Model Inference Batch

**Scenario**: A data science team needs to run predictions on 50,000 customer records.

**Job Submission**:
```json
POST /api/v1/jobs
{
  "job_type": "ml_inference",
  "total_tasks": 50000,
  "parameters": {
    "work_type": "cpu_bound",
    "duration_seconds": 1,
    "model_version": "v2.3",
    "batch_size": 100
  }
}
```

**What Happens**:
1. Job splits 50,000 records into 500 tasks (100 records per task)
2. Workers process tasks concurrently across 100 Kubernetes pods
3. Results written to database
4. Failed tasks automatically retried (up to 3 times)
5. Analytics shows processing rate, success rate, average time

### Common Patterns

All scenarios follow the same pattern:
1. **Submit Job** → System creates job and tasks
2. **Queue Tasks** → Tasks enqueued to SQS for reliable delivery
3. **Scale Workers** → Kubernetes auto-scales workers based on queue depth
4. **Process in Parallel** → Multiple workers process tasks simultaneously
5. **Track Progress** → Real-time dashboard shows completion status
6. **Handle Failures** → Automatic retries and dead-letter queue for failed tasks
7. **Complete Job** → Job status updates when all tasks finish

## Architecture

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI       │────▶│ Step Functions│────▶│     SQS     │
│   Backend       │     │  (Orchestrator)│     │   (Queue)   │
└─────────────────┘     └──────────────┘     └──────┬───────┘
       │                                              │
       │                                              ▼
       │                                    ┌─────────────────┐
       │                                    │  Kubernetes     │
       └────────────────────────────────────│    Workers      │
                                            │  (Task Process) │
                                            └─────────────────┘
```

### Component Details

**Frontend (React + TypeScript)**
- Job submission form
- Job list with real-time status updates
- Job detail view with task progress
- Analytics dashboard with charts

**Backend API (FastAPI)**
- RESTful endpoints for job management
- Database integration (PostgreSQL/SQLite)
- Step Functions workflow initiation
- Task status tracking

**AWS Step Functions**
- Orchestrates job lifecycle
- States: CREATE_TASKS → ENQUEUE_TASKS → MONITOR → COMPLETE/FAIL

**AWS SQS**
- Task queue for worker consumption
- Dead-letter queue for failed tasks
- Long polling for efficient message retrieval

**Kubernetes Workers**
- Poll SQS for tasks
- Execute compute workloads
- Report completion via API
- Horizontal scaling support

**Data Storage**
- PostgreSQL (local dev): SQL tables
- DynamoDB (production): NoSQL tables with GSIs

## Tech Stack

### Backend
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM for database operations
- **SQLite/PostgreSQL** - Job and task metadata storage
- **Alembic** - Database migrations

### Frontend
- **React** + **TypeScript** - UI framework
- **Vite** - Build tool
- **Recharts** - Analytics visualizations
- **Axios** - API client

### Infrastructure
- **AWS Step Functions** - Workflow orchestration
- **AWS SQS** - Message queue
- **Kubernetes (kind)** - Container orchestration
- **LocalStack** - Local AWS emulation
- **Terraform** - Infrastructure as Code

### Worker
- **Python** - Task processing logic
- **boto3** - AWS SDK for SQS
- **NumPy** - Matrix operations (for demo workloads)

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- kubectl & kind (for Kubernetes)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/suhasramanand/orchestrator.git
   cd orchestrator
   ```

2. **Start the database**
   ```bash
   docker-compose up -d postgres
   ```

3. **Set up backend** (see [Backend Setup](#backend-setup))

4. **Set up frontend** (see [Frontend Setup](#frontend-setup))

5. **Set up LocalStack and Kubernetes** (see [LocalStack Setup](#localstack-setup) and [Kubernetes Setup](#kubernetes-setup))

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Detailed Setup Guide

### Backend Setup

#### Create Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment
Create a `.env` file in the `backend` directory:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobdb
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

#### Run Database Migrations
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobdb
python -m alembic upgrade head
```

Or for SQLite (simpler for local testing):
```bash
python -c "from app.db.database import create_db_and_tables; create_db_and_tables()"
```

#### Start Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Start Development Server
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### LocalStack Setup

LocalStack provides local AWS service emulation for development and testing.

#### Start LocalStack
```bash
docker-compose -f docker-compose.localstack.yml up -d
```

#### Wait for LocalStack to be ready
```bash
curl http://localhost:4566/_localstack/health
```

#### Create SQS Queue
```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name tasks \
    --region us-east-1
```

#### Get Queue URL
```bash
aws --endpoint-url=http://localhost:4566 sqs get-queue-url \
    --queue-name tasks \
    --region us-east-1 \
    --query 'QueueUrl' \
    --output text
```

#### Create Dead Letter Queue
```bash
aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name tasks-dlq \
    --region us-east-1
```

#### Automated Setup
Use the provided script:
```bash
./setup_localstack.sh
```

### Kubernetes Setup

#### Prerequisites
- Docker Desktop running
- kind installed: `brew install kind` (macOS) or see [kind installation](https://kind.sigs.k8s.io/)

#### Create Cluster
```bash
./setup_k8s.sh
```

Or manually:
```bash
kind create cluster --name job-orchestration --wait 5m
```

#### Verify Cluster
```bash
kubectl cluster-info
kubectl get nodes
```

### Worker Deployment

#### Option A: Run Worker Locally

Create a `.env` file in the `worker` directory:
```bash
cd worker
cat > .env << EOF
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
SQS_QUEUE_URL=http://localhost:4566/000000000000/tasks
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

#### Option B: Deploy to Kubernetes

1. **Build Worker Docker Image**
   ```bash
   cd worker
   docker build -t job-worker:latest .
   ```

2. **Load Image into kind**
   ```bash
   kind load docker-image job-worker:latest --name job-orchestration
   ```

3. **Create Kubernetes Secrets**
   ```bash
   kubectl create secret generic aws-credentials \
     --from-literal=access-key-id=test \
     --from-literal=secret-access-key=test
   ```

4. **Create ConfigMap**
   ```bash
   kubectl create configmap job-worker-config \
     --from-literal=AWS_REGION=us-east-1 \
     --from-literal=API_BASE_URL=http://host.docker.internal:8000 \
     --from-literal=SQS_QUEUE_URL=http://localstack:4566/000000000000/tasks
   ```

5. **Deploy Worker**
   ```bash
   kubectl apply -f infra/k8s/deployment.yaml
   ```

6. **Check Worker Status**
   ```bash
   kubectl get pods -l app=job-worker
   kubectl logs -f deployment/job-worker
   ```

#### Kubernetes Network Configuration

For workers in Kubernetes to reach LocalStack, you need to:

1. **Connect LocalStack to kind network**
   ```bash
   docker network connect kind localstack
   ```

2. **Create Kubernetes Service for LocalStack**
   ```bash
   kubectl apply -f infra/k8s/localstack-service.yaml
   ```

3. **Update ConfigMap with correct queue URL**
   ```bash
   kubectl patch configmap job-worker-config --type merge \
     -p '{"data":{"SQS_QUEUE_URL":"http://localstack:4566/000000000000/tasks"}}'
   ```

## Project Structure

```
orchestrator/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── db/          # Database models and connection
│   │   ├── models/      # Pydantic schemas
│   │   ├── routes/      # API endpoints
│   │   ├── services/     # Business logic
│   │   └── utils/       # Configuration and utilities
│   └── alembic/         # Database migrations
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API client
│   │   └── types/       # TypeScript types
│   └── public/
├── worker/              # Kubernetes worker
│   └── worker.py        # SQS polling and task processing
├── infra/               # Infrastructure as Code
│   ├── k8s/            # Kubernetes manifests
│   └── terraform/      # AWS Terraform configs
├── screenshots/         # UI screenshots
├── ui-demo.mp4         # Demo video
└── scripts/            # Setup and utility scripts
```

## API Endpoints

### Jobs
- `POST /api/v1/jobs` - Create a new job
- `GET /api/v1/jobs` - List jobs (with pagination and search)
- `GET /api/v1/jobs/{job_id}` - Get job details

### Tasks
- `GET /api/v1/jobs/{job_id}/tasks` - Get tasks for a job
- `POST /api/v1/tasks/{task_id}/running` - Mark task as running
- `POST /api/v1/tasks/{task_id}/complete` - Mark task as complete
- `POST /api/v1/tasks/{task_id}/failed` - Mark task as failed

### Analytics
- `GET /api/v1/analytics/overview` - Overview statistics
- `GET /api/v1/analytics/jobs-by-type` - Jobs grouped by type
- `GET /api/v1/analytics/jobs-by-status` - Jobs grouped by status
- `GET /api/v1/analytics/tasks-by-status` - Tasks grouped by status
- `GET /api/v1/analytics/timeline?days=7` - Job creation timeline
- `GET /api/v1/analytics/processing-time-stats` - Processing time statistics

## How It Works

### Job Creation Flow

1. User submits job via frontend → Backend API
2. Backend creates job record in database (status: PENDING)
3. Backend initiates Step Functions execution (or creates tasks locally)
4. Step Functions Lambda creates task records
5. Step Functions enqueues tasks to SQS
6. Job status updated to ENQUEUED

### Task Processing Flow

1. Worker polls SQS (long polling, 20s wait)
2. Worker receives task message
3. Worker marks task as RUNNING via API
4. Worker processes task (simulated computation)
5. Worker marks task as COMPLETED via API
6. Worker deletes message from SQS
7. Backend updates job completion stats
8. When all tasks complete, job status → COMPLETED

### Error Handling

1. **Task Failure**:
   - Worker catches exception
   - Worker marks task as FAILED via API
   - Message deleted from SQS (or sent to DLQ after max retries)
   - Job tracks failed task count

2. **Worker Failure**:
   - SQS visibility timeout expires
   - Message becomes visible again
   - Another worker picks it up
   - Retry count incremented

3. **Backend Failure**:
   - Worker retries API call with exponential backoff
   - Task remains in SQS until processed

## Development Notes

### Key Design Decisions

1. **SQLite for Local Development**: Started with SQLite for rapid iteration, added PostgreSQL support later
2. **LocalStack Integration**: Early integration of LocalStack for SQS emulation
3. **Kubernetes Network Challenges**: Required custom service/endpoints configuration for LocalStack connectivity
4. **Health Check Removal**: Removed liveness/readiness probes from worker deployment as they caused restart loops

### Critical Issues Resolved

1. **Task Enqueueing**: Fixed issue where tasks were created but not sent to SQS
2. **Network Connectivity**: Resolved Kubernetes pod to LocalStack connection issues
3. **Message Deletion**: Fixed bug where messages were deleted even when API calls failed
4. **API Connectivity**: Standardized API URL configuration for Kubernetes workers
5. **Health Check Failures**: Removed problematic health checks from worker deployment

### Testing

1. **Create a Job via API**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/jobs \
     -H "Content-Type: application/json" \
     -d '{"job_type": "compute", "num_tasks": 5, "parameters": {"work_type": "cpu_bound", "work_duration_seconds": 1.0}}'
   ```

2. **Check Job Status**:
   ```bash
   curl http://localhost:8000/api/v1/jobs/{job_id}
   ```

3. **Monitor Worker Logs**:
   ```bash
   kubectl logs -f deployment/job-worker
   ```

### Troubleshooting

**Backend Issues**
- Ensure Postgres is running: `docker ps | grep postgres`
- Check DATABASE_URL in `.env`
- Verify migrations: `python -m alembic upgrade head`

**Frontend Issues**
- Ensure backend is running on port 8000
- Check CORS settings in backend

**Worker Issues**
- Verify SQS_QUEUE_URL is correct
- If using LocalStack, ensure it's running: `curl http://localhost:4566/_localstack/health`
- Check API_BASE_URL is accessible from worker

**Kubernetes Issues**
- Verify image is loaded: `kind load docker-image job-worker:latest`
- Check pod logs: `kubectl logs <pod-name>`
- Verify secrets and configmaps exist

## Resume Highlights

This project demonstrates:
- **Distributed Systems**: Job orchestration, task distribution, worker pooling
- **Cloud Architecture**: AWS Step Functions, SQS, Lambda integration
- **Container Orchestration**: Kubernetes deployments, ConfigMaps, Services
- **Full-Stack Development**: FastAPI backend, React frontend
- **Infrastructure as Code**: Terraform for AWS resources
- **CI/CD**: GitHub Actions workflows
- **Local Development**: LocalStack, kind, Docker Compose
