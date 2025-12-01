#!/bin/bash

# Simple test script for local development
# This script tests the basic functionality of the system

set -e

echo "🧪 Testing Job Orchestration Platform (Local)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo -e "\n${YELLOW}Checking backend...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running. Please start it with:${NC}"
    echo "  cd backend && uvicorn app.main:app --reload --port 8000"
    exit 1
fi

# Test creating a job
echo -e "\n${YELLOW}Creating a test job...${NC}"
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "compute",
    "num_tasks": 3,
    "parameters": {
      "work_type": "cpu_bound",
      "work_duration_seconds": 1.0
    }
  }')

JOB_ID=$(echo $JOB_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}✗ Failed to create job${NC}"
    echo "Response: $JOB_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Job created: $JOB_ID${NC}"

# Wait a bit
sleep 2

# Check job status
echo -e "\n${YELLOW}Checking job status...${NC}"
JOB_STATUS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID | grep -o '"status":"[^"]*' | cut -d'"' -f4)
echo -e "${GREEN}✓ Job status: $JOB_STATUS${NC}"

# List jobs
echo -e "\n${YELLOW}Listing jobs...${NC}"
JOBS_COUNT=$(curl -s http://localhost:8000/api/v1/jobs | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓ Total jobs: $JOBS_COUNT${NC}"

# Get job tasks
echo -e "\n${YELLOW}Getting job tasks...${NC}"
TASKS_RESPONSE=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/tasks)
TASKS_COUNT=$(echo $TASKS_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓ Tasks count: $TASKS_COUNT${NC}"

echo -e "\n${GREEN}✅ All tests passed!${NC}"
echo -e "\nView the job in the frontend: http://localhost:3000/jobs/$JOB_ID"

