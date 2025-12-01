# Distributed Job Orchestration Platform

A production-ready distributed job orchestration system that combines AWS Serverless services (Step Functions, SQS, Lambda) with Kubernetes for scalable compute. Users submit jobs via REST API, which are automatically broken into parallel tasks, orchestrated through AWS Step Functions, queued in SQS, and processed by Kubernetes workers.

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

### Key Features

- ✅ **REST API** for job submission and status tracking
- ✅ **AWS Step Functions** for workflow orchestration
- ✅ **SQS** for reliable task queuing
- ✅ **Kubernetes** for scalable worker deployment
- ✅ **Real-time Dashboard** with React frontend
- ✅ **Analytics** with charts and metrics
- ✅ **Local Development** support with LocalStack and kind

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

3. **Set up backend**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python -c "from app.db.database import create_db_and_tables; create_db_and_tables()"
   uvicorn app.main:app --reload --port 8000
   ```

4. **Set up frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Set up LocalStack and Kubernetes** (see [LOCALSTACK_SETUP.md](./LOCALSTACK_SETUP.md) and [K8S_SETUP_GUIDE.md](./K8S_SETUP_GUIDE.md))

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

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
└── docs/               # Documentation
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

1. **Job Submission**: User creates a job via the web UI or API, specifying:
   - Job type (compute, data_processing, ml_inference)
   - Number of tasks to create
   - Work type (CPU-bound, I/O-bound, matrix multiplication)
   - Duration and parameters

2. **Task Creation**: Backend creates individual tasks and enqueues them to SQS

3. **Worker Processing**: Kubernetes workers continuously poll SQS for tasks:
   - Receive task message
   - Mark task as "RUNNING" via API
   - Execute the work (simulated computation)
   - Mark task as "COMPLETED" or "FAILED"
   - Delete message from SQS

4. **Status Updates**: Job status automatically updates as tasks complete

5. **Monitoring**: Real-time dashboard shows job progress, analytics, and metrics

## Local Development

For local development without AWS:
- **LocalStack** emulates SQS
- **SQLite** replaces PostgreSQL (optional)
- **kind** provides local Kubernetes cluster
- Workers connect to LocalStack via Kubernetes service

See [SETUP_LOCAL.md](./SETUP_LOCAL.md) for detailed setup instructions.

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and design
- [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md) - Visual architecture diagrams
- [SETUP_LOCAL.md](./SETUP_LOCAL.md) - Local development setup
- [LOCALSTACK_SETUP.md](./LOCALSTACK_SETUP.md) - LocalStack configuration
- [K8S_SETUP_GUIDE.md](./K8S_SETUP_GUIDE.md) - Kubernetes setup
- [PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md) - Comprehensive project documentation
- [SCREENSHOTS.md](./SCREENSHOTS.md) - UI screenshots and demo video

## Screenshots

See the [screenshots/](./screenshots/) directory for UI screenshots and [ui-demo.mp4](./ui-demo.mp4) for a video walkthrough.

## Resume Highlights

This project demonstrates:
- **Distributed Systems**: Job orchestration, task distribution, worker pooling
- **Cloud Architecture**: AWS Step Functions, SQS, Lambda integration
- **Container Orchestration**: Kubernetes deployments, ConfigMaps, Services
- **Full-Stack Development**: FastAPI backend, React frontend
- **Infrastructure as Code**: Terraform for AWS resources
- **CI/CD**: GitHub Actions workflows
- **Local Development**: LocalStack, kind, Docker Compose

## License

MIT

## Author

Built as a portfolio project demonstrating distributed systems and cloud architecture.
