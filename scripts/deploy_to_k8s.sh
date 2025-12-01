#!/bin/bash
set -e

echo "🚀 Deploying Job Orchestration Worker to Kubernetes"
echo "===================================================="
echo ""

# Check if kind cluster exists
if ! kind get clusters | grep -q job-orchestration; then
    echo "❌ Cluster 'job-orchestration' not found"
    echo "   Run: ./setup_k8s.sh first"
    exit 1
fi

# Set kubeconfig
export KUBECONFIG=$(kind get kubeconfig --name job-orchestration)
kubectl cluster-info --context kind-job-orchestration > /dev/null

echo "✅ Connected to cluster"
echo ""

# Build worker image
echo "🔨 Building worker Docker image..."
cd worker
docker build -t job-worker:latest . || {
    echo "❌ Failed to build image"
    exit 1
}
echo "✅ Image built: job-worker:latest"
echo ""

# Load image into kind
echo "📦 Loading image into kind cluster..."
kind load docker-image job-worker:latest --name job-orchestration
echo "✅ Image loaded into cluster"
echo ""

# Go to k8s manifests
cd ../infra/k8s

# Create ConfigMap
echo "📝 Creating ConfigMap..."
kubectl apply -f configmap.yaml
echo "✅ ConfigMap created"
echo ""

# Create Secret (with dummy values for local testing)
echo "🔐 Creating Secret..."
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id=test \
  --from-literal=secret-access-key=test \
  --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Secret created"
echo ""

# Update ConfigMap with local backend URL
echo "🔧 Updating ConfigMap for local backend..."
kubectl patch configmap job-worker-config --type merge -p '{"data":{"API_BASE_URL":"http://host.docker.internal:8000"}}'
echo "✅ ConfigMap updated"
echo ""

# Deploy worker
echo "🚀 Deploying worker..."
kubectl apply -f deployment.yaml
echo "✅ Deployment created"
echo ""

# Wait for pods
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=job-worker --timeout=60s || true

echo ""
echo "📊 Deployment Status:"
kubectl get pods -l app=job-worker
kubectl get deployments
echo ""

echo "✅ Worker deployed successfully!"
echo ""
echo "📝 Useful commands:"
echo "   kubectl get pods -l app=job-worker"
echo "   kubectl logs -f deployment/job-worker"
echo "   kubectl describe pod -l app=job-worker"
