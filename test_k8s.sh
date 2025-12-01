#!/bin/bash
echo "🧪 Testing Kubernetes Deployment"
echo "================================"
echo ""

export KUBECONFIG=$(kind get kubeconfig --name job-orchestration)

echo "1️⃣  Checking cluster status..."
kubectl cluster-info --context kind-job-orchestration > /dev/null && echo "✅ Cluster is running" || echo "❌ Cluster not accessible"

echo ""
echo "2️⃣  Checking worker pods..."
PODS=$(kubectl get pods -l app=job-worker --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "$PODS" -gt 0 ]; then
    echo "✅ Found $PODS worker pod(s)"
    kubectl get pods -l app=job-worker
else
    echo "❌ No worker pods found"
fi

echo ""
echo "3️⃣  Checking backend API..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is accessible"
else
    echo "❌ Backend not accessible (make sure it's running on port 8000)"
fi

echo ""
echo "4️⃣  Creating a test job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_type": "k8s-test", "num_tasks": 3, "parameters": {"work_type": "cpu_bound", "work_duration_seconds": 1.0}}')

if echo "$JOB_RESPONSE" | grep -q "id"; then
    JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
    echo "✅ Job created: $JOB_ID"
    echo ""
    echo "5️⃣  Checking worker logs for activity..."
    kubectl logs -l app=job-worker --tail=10 2>&1 | tail -5
else
    echo "❌ Failed to create job"
    echo "Response: $JOB_RESPONSE"
fi

echo ""
echo "✅ Test complete!"
echo ""
echo "📝 Useful commands:"
echo "   kubectl get pods -l app=job-worker"
echo "   kubectl logs -f deployment/job-worker"
echo "   kubectl describe pod -l app=job-worker"
