#!/bin/bash
set -e

export KUBECONFIG=$(kind get kubeconfig --name job-orchestration)

echo "Fixing LocalStack connection for Kubernetes workers"
echo "====================================================="
echo ""

# Get LocalStack container IP
LOCALSTACK_IP=$(docker inspect localstack | grep -A 5 "Networks" | grep "IPAddress" | head -1 | awk '{print $2}' | tr -d '",')

if [ -z "$LOCALSTACK_IP" ]; then
    # Try alternative method
    LOCALSTACK_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' localstack 2>/dev/null)
fi

if [ -z "$LOCALSTACK_IP" ]; then
    echo "Could not get LocalStack IP, using host.docker.internal"
    QUEUE_URL="http://host.docker.internal:4566/000000000000/tasks"
else
    echo "Found LocalStack IP: $LOCALSTACK_IP"
    QUEUE_URL="http://$LOCALSTACK_IP:4566/000000000000/tasks"
fi

echo "Queue URL: $QUEUE_URL"
echo ""

# Update deployment
echo "Updating deployment..."
kubectl set env deployment/job-worker SQS_QUEUE_URL="$QUEUE_URL"

echo "Deployment updated"
echo ""
echo "Waiting for pods to restart..."
sleep 5

kubectl get pods -l app=job-worker

echo ""
echo "Check logs:"
echo "   kubectl logs -f deployment/job-worker"
