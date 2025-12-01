# 🚀 Running the Demo

## Current Status

✅ **Frontend**: Running on http://localhost:3000
⚠️  **Backend**: Needs to be started manually

## Start Backend

```bash
cd backend
source venv/bin/activate
export DATABASE_URL=sqlite:///./jobdb.db
uvicorn app.main:app --reload --port 8000
```

## Start Frontend (if not running)

```bash
cd frontend
npm run dev
```

## Test the System

1. **Open Frontend**: http://localhost:3000
2. **Create a Job**: Click "Create Job" button
3. **View Jobs**: See the job list with real-time updates
4. **View Details**: Click on a job to see task progress

## API Endpoints

- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **List Jobs**: http://localhost:8000/api/v1/jobs
- **Create Job**: 
  ```bash
  curl -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d '{"job_type": "compute", "num_tasks": 5, "parameters": {"work_type": "cpu_bound", "work_duration_seconds": 1.0}}'
  ```

## What You'll See

- Jobs being created and tracked
- Task status updates (when workers are running)
- Real-time progress bars
- Job completion status

## Next: Add Workers

To see tasks actually processing, you need to run workers:

```bash
cd worker
source venv/bin/activate
export SQS_QUEUE_URL=<your-sqs-url>
export API_BASE_URL=http://localhost:8000
python worker.py
```

Or deploy to Kubernetes using the manifests in `infra/k8s/`
