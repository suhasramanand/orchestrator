# Kubernetes Status

## Current Status: ❌ NOT RUNNING

### What's Running:
- ✅ Backend API (FastAPI) - http://localhost:8000
- ✅ Frontend (React) - http://localhost:3000
- ❌ Kubernetes Cluster - NOT RUNNING
- ❌ Worker Pods - NOT DEPLOYED

### What You Need:

1. **Kubernetes Cluster** (choose one):
   - **kind**: `kind create cluster`
   - **minikube**: `minikube start`
   - **Docker Desktop**: Enable Kubernetes in settings

2. **Docker** (required for kind/minikube):
   - Docker Desktop must be running

3. **Deploy Worker**:
   - Build Docker image
   - Load into cluster
   - Apply Kubernetes manifests

## Quick Start Guide

### Option 1: Using kind (Recommended for local)

```bash
# 1. Install kind (if not installed)
brew install kind  # macOS
# or: go install sigs.k8s.io/kind@latest

# 2. Create cluster
kind create cluster --name job-orchestration

# 3. Build worker image
cd worker
docker build -t job-worker:latest .

# 4. Load image into kind
kind load docker-image job-worker:latest --name job-orchestration

# 5. Deploy worker
cd ../infra/k8s
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml

# 6. Check status
kubectl get pods -l app=job-worker
kubectl logs -f deployment/job-worker
```

### Option 2: Using minikube

```bash
# 1. Start minikube
minikube start

# 2. Build worker image (minikube will use its Docker daemon)
eval $(minikube docker-env)
cd worker
docker build -t job-worker:latest .

# 3. Deploy
cd ../infra/k8s
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
```

### Option 3: Docker Desktop Kubernetes

1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Enable Kubernetes
4. Wait for it to start
5. Build and deploy as above

## Current Architecture

```
┌─────────────┐
│  Frontend   │ ✅ Running (localhost:3000)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Backend   │ ✅ Running (localhost:8000)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │ ✅ Running (SQLite)
└─────────────┘

┌─────────────┐
│ Kubernetes  │ ❌ NOT RUNNING
│   Workers   │ ❌ NOT DEPLOYED
└─────────────┘
```

## To See Full System Working

You need:
1. Kubernetes cluster running
2. Worker pods deployed
3. SQS queue (LocalStack or AWS)
4. Workers configured to poll SQS

Right now, jobs are created but tasks won't process until workers are running.
