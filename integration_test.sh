#!/bin/bash
set -e

echo "Submitting job..."
response=$(curl -s -X POST http://localhost:3000/submit)
JOB_ID=$(echo "$response" | jq -r .job_id)

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
  echo "ERROR: Failed to get job ID. Response: $response"
  exit 1
fi

echo "Job submitted: $JOB_ID"

TIMEOUT=30
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  status=$(curl -s "http://localhost:3000/status/$JOB_ID" | jq -r .status)
  echo "Status: $status"
  if [ "$status" = "completed" ]; then
    echo "Integration test passed!"
    exit 0
  fi
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done

echo "ERROR: Job did not complete within ${TIMEOUT}s"
exit 1
