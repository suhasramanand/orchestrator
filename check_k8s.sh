#!/bin/bash
echo "🔍 Checking Kubernetes Status"
echo "=============================="
echo ""

# Check kubectl
if command -v kubectl &> /dev/null; then
    echo "✅ kubectl is installed"
    kubectl version --client --short 2>/dev/null
else
    echo "❌ kubectl is not installed"
    echo "   Install: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

echo ""

# Check cluster
echo "📡 Cluster Status:"
if kubectl cluster-info &> /dev/null; then
    echo "✅ Kubernetes cluster is running"
    kubectl cluster-info 2>&1 | head -1
    echo ""
    echo "📊 Nodes:"
    kubectl get nodes 2>&1
else
    echo "❌ No Kubernetes cluster found"
    echo ""
    echo "💡 To start a local cluster:"
    echo "   - kind: kind create cluster"
    echo "   - minikube: minikube start"
    echo "   - Docker Desktop: Enable Kubernetes in settings"
    exit 1
fi

echo ""
echo "📦 Deployed Resources:"
kubectl get pods,deployments,services,configmaps -n default 2>&1 | grep -E "job-worker|backend|NAME" || echo "No job-worker resources deployed"

echo ""
echo "🚀 To deploy the worker:"
echo "   1. Build image: cd worker && docker build -t job-worker:latest ."
echo "   2. Load into kind: kind load docker-image job-worker:latest"
echo "   3. Apply manifests: kubectl apply -f infra/k8s/"
