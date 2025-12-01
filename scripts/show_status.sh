#!/bin/bash
echo "📊 Job Orchestration Platform Status"
echo "===================================="
echo ""

# Backend health
echo "🔍 Backend Health:"
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ Backend not responding"
echo ""

# List jobs
echo "📋 Recent Jobs:"
curl -s http://localhost:8000/api/v1/jobs?page=1&page_size=5 | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'jobs' in data:
    print(f\"Total: {data['total']} jobs\")
    for job in data['jobs'][:3]:
        print(f\"  - {job['id'][:8]}... | {job['status']} | {job['completed_tasks']}/{job['total_tasks']} tasks\")
else:
    print('No jobs found')
" 2>/dev/null || echo "❌ Could not fetch jobs"
echo ""

# Frontend check
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "⚠️  Frontend not running. Start with: cd frontend && npm run dev"
fi
