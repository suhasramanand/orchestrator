#!/bin/bash
set -e

echo "🚀 Setting up Local Kubernetes Cluster"
echo "========================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "   Install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "   Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Install kind if not present
if ! command -v kind &> /dev/null; then
    echo "📦 Installing kind..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install kind
    else
        echo "Please install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
        exit 1
    fi
fi

echo "✅ kind is installed: $(kind --version)"
echo ""

# Check if cluster already exists
if kind get clusters | grep -q job-orchestration; then
    echo "⚠️  Cluster 'job-orchestration' already exists"
    read -p "Delete and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kind delete cluster --name job-orchestration
    else
        echo "Using existing cluster"
        kind get kubeconfig --name job-orchestration > /tmp/kind-kubeconfig
        export KUBECONFIG=/tmp/kind-kubeconfig
        kubectl cluster-info
        exit 0
    fi
fi

# Create cluster
echo "🔧 Creating kind cluster..."
kind create cluster --name job-orchestration --wait 5m

# Set kubeconfig
export KUBECONFIG=$(kind get kubeconfig --name job-orchestration)
kubectl cluster-info --context kind-job-orchestration

echo ""
echo "✅ Kubernetes cluster is ready!"
echo ""
echo "📊 Cluster info:"
kubectl get nodes
