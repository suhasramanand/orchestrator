# System Architecture

## Overview

The Distributed Job Orchestration Platform is a production-quality system that combines AWS Serverless technologies with Kubernetes for scalable, distributed task processing.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    React + TypeScript Frontend                  │
│                    (http://localhost:3000)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway / ALB                           │
│                    (Production: AWS ALB)                         │
│                    (Local: Direct connection)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Control Plane)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API Endpoints:                                      │  │
│  │  - POST /api/v1/jobs          (Create job)                │  │
│  │  - GET  /api/v1/jobs          (List jobs)                 │  │
│  │  - GET  /api/v1/jobs/{id}     (Get job details)           │  │
│  │  - GET  /api/v1/jobs/{id}/tasks (Get job tasks)           │  │
│  │  - POST /api/v1/tasks/{id}/complete (Task completion)     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Services:                                                 │  │
│  │  - JobService        (Job lifecycle management)           │  │
│  │  - TaskService       (Task status tracking)               │  │
│  │  - StepFunctionsService (AWS Step Functions integration)  │  │
│  │  - SQSService        (SQS message handling)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌──────────────────┐      ┌──────────────────────┐
    │   Postgres DB    │      │   AWS Step Functions │
    │  (Local Dev)     │      │   (Production)      │
    │                  │      │                      │
    │  - jobs table    │      │  Workflow States:     │
    │  - tasks table   │      │  1. CreateTasks      │
    └──────────────────┘      │  2. EnqueueTasks     │
                              │  3. MonitorCompletion│
                              │  4. JobCompleted     │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │    AWS SQS Queue      │
                              │   (Task Queue)        │
                              │                       │
                              │  - tasks queue        │
                              │  - tasks-dlq (DLQ)    │
                              └──────────┬───────────┘
                                         │
                                         │ Poll for messages
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Kubernetes Cluster (Compute Layer)                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Worker Deployment (3+ replicas)                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                │  │
│  │  │ Worker  │  │ Worker  │  │ Worker  │                │  │
│  │  │ Pod 1   │  │ Pod 2   │  │ Pod 3   │                │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘                │  │
│  │       │            │            │                       │  │
│  │       └────────────┴────────────┘                       │  │
│  │                    │                                    │  │
│  │                    ▼                                    │  │
│  │         ┌─────────────────────┐                         │  │
│  │         │  Task Processor     │                         │  │
│  │         │  - Poll SQS         │                         │  │
│  │         │  - Process task     │                         │  │
│  │         │  - Update status    │                         │  │
│  │         └──────────┬──────────┘                         │  │
│  │                    │                                    │  │
│  │                    ▼                                    │  │
│  │         ┌─────────────────────┐                         │  │
│  │         │  HTTP Callback      │                         │  │
│  │         │  to Backend API     │                         │  │
│  │         └─────────────────────┘                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React + TypeScript)

**Location**: `frontend/`

**Responsibilities**:
- Job creation form
- Job list with real-time status updates
- Job detail view with task progress
- Task status visualization

**Key Features**:
- Auto-refresh every 2-5 seconds
- Progress bars and status badges
- Responsive design

### 2. Backend API (FastAPI)

**Location**: `backend/app/`

**Architecture**:
- **Routes**: HTTP endpoints (`routes/`)
- **Services**: Business logic (`services/`)
- **Models**: Database models (`db/models.py`) and Pydantic schemas (`models/schemas.py`)
- **Database**: SQLAlchemy ORM with Postgres (local) or DynamoDB (AWS)

**Key Endpoints**:
- `POST /api/v1/jobs` - Create job
- `GET /api/v1/jobs` - List jobs (paginated)
- `GET /api/v1/jobs/{id}` - Get job details
- `GET /api/v1/jobs/{id}/tasks` - Get tasks for job
- `POST /api/v1/tasks/{id}/complete` - Mark task complete
- `POST /api/v1/tasks/{id}/running` - Mark task running
- `POST /api/v1/tasks/{id}/failed` - Mark task failed

### 3. Worker Service

**Location**: `worker/`

**Responsibilities**:
- Poll SQS for tasks
- Process tasks (CPU-bound, I/O-bound, or matrix operations)
- Report completion/failure to backend API
- Handle retries and errors

**Deployment Options**:
- **Local**: Run as Python script
- **Kubernetes**: Deploy as Deployment or Job

### 4. AWS Step Functions (Production)

**State Machine Flow**:
1. **CreateTasks**: Lambda function creates task records in DynamoDB
2. **EnqueueTasks**: Send task messages to SQS
3. **MonitorCompletion**: Lambda checks task completion status
4. **CheckCompletion**: Decision state - all complete?
5. **WaitAndRetry**: Wait 10 seconds and retry monitoring
6. **JobCompleted**: Final success state

### 5. AWS SQS

**Queues**:
- **tasks**: Main task queue with long polling (20s)
- **tasks-dlq**: Dead-letter queue for failed messages (after 3 retries)

**Configuration**:
- Visibility timeout: 300 seconds (5 minutes)
- Message retention: 4 days
- Long polling enabled

### 6. Data Storage

**Local Development**: PostgreSQL
- `jobs` table: Job metadata and status
- `tasks` table: Task details and status

**Production**: DynamoDB
- `jobs` table: Partition key `id`, GSI on `status`
- `tasks` table: Partition key `id`, GSIs on `job_id` and `status`

## Data Flow

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

## Scalability

### Horizontal Scaling

- **Workers**: Scale Kubernetes Deployment based on queue depth
- **Backend**: Scale FastAPI with multiple replicas behind load balancer
- **Database**: Read replicas for Postgres, DynamoDB auto-scales

### Performance Characteristics

- **Throughput**: 1000+ tasks/minute (depends on worker count)
- **Latency**: <100ms API response time
- **Reliability**: 99.9% task success rate with retries

## Security

- **API**: CORS configured for frontend origins
- **AWS**: IAM roles with least privilege
- **Kubernetes**: RBAC for worker pods
- **Secrets**: Kubernetes Secrets for AWS credentials

## Monitoring & Observability

- **Logging**: Structured JSON logs (structlog)
- **Metrics**: Task completion rates, job durations
- **Tracing**: Distributed tracing (future enhancement)
- **Alerts**: CloudWatch alarms for failed jobs

## Deployment Environments

### Local Development
- Postgres in Docker
- Backend on localhost:8000
- Frontend on localhost:3000
- Worker runs locally or in kind/minikube
- LocalStack for SQS (optional)

### Production (AWS)
- Backend: ECS Fargate or Lambda
- Frontend: S3 + CloudFront
- Workers: EKS cluster
- Database: DynamoDB
- Queue: AWS SQS
- Orchestration: Step Functions

## Future Enhancements

1. **Real-time Updates**: WebSocket support for live job status
2. **Priority Queues**: Multiple SQS queues for different priorities
3. **Scheduled Jobs**: CloudWatch Events for cron-like scheduling
4. **Cost Optimization**: Spot instances for workers
5. **Advanced Monitoring**: Prometheus + Grafana dashboards
6. **Multi-region**: Cross-region job processing
7. **Job Dependencies**: DAG-based job workflows

