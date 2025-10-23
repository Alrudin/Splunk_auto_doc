#!/bin/bash
# Demo script for Background Worker Service
# This script demonstrates the complete workflow of uploading, parsing, and monitoring

set -e

echo "=========================================="
echo "  Splunk Auto Doc - Worker Service Demo"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
SAMPLE_FILE="${1:-}"

if [ -z "$SAMPLE_FILE" ]; then
    echo -e "${YELLOW}Usage: $0 <path-to-config-archive>${NC}"
    echo ""
    echo "This script demonstrates the worker service by:"
    echo "  1. Uploading a Splunk configuration archive"
    echo "  2. Monitoring the parsing task"
    echo "  3. Showing the parsed results"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/splunk_config.tar.gz"
    echo ""
    exit 1
fi

if [ ! -f "$SAMPLE_FILE" ]; then
    echo "Error: File not found: $SAMPLE_FILE"
    exit 1
fi

echo -e "${BLUE}Step 1: Checking API availability${NC}"
if ! curl -s -f "$API_URL/health" > /dev/null; then
    echo "Error: API not available at $API_URL"
    echo "Please start services with: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ API is running${NC}"
echo ""

echo -e "${BLUE}Step 2: Checking worker health${NC}"
WORKER_HEALTH=$(curl -s "$API_URL/v1/worker/health" || echo '{"status":"unavailable"}')
WORKER_STATUS=$(echo "$WORKER_HEALTH" | jq -r '.status // "unavailable"')

if [ "$WORKER_STATUS" = "healthy" ]; then
    WORKER_COUNT=$(echo "$WORKER_HEALTH" | jq -r '.workers // 0')
    echo -e "${GREEN}✓ Worker is healthy (${WORKER_COUNT} workers active)${NC}"
else
    echo -e "${YELLOW}⚠ Worker may not be available${NC}"
    echo "Proceeding anyway - parsing will be queued..."
fi
echo ""

echo -e "${BLUE}Step 3: Uploading configuration archive${NC}"
echo "File: $SAMPLE_FILE"
echo "Size: $(du -h "$SAMPLE_FILE" | cut -f1)"
echo ""

UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/v1/uploads" \
  -F "file=@$SAMPLE_FILE" \
  -F "type=ds_etc" \
  -F "label=Demo Upload")

RUN_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.id')
INITIAL_STATUS=$(echo "$UPLOAD_RESPONSE" | jq -r '.status')

if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
    echo "Error: Upload failed"
    echo "$UPLOAD_RESPONSE" | jq .
    exit 1
fi

echo -e "${GREEN}✓ Upload successful${NC}"
echo "Run ID: $RUN_ID"
echo "Status: $INITIAL_STATUS"
echo ""

echo -e "${BLUE}Step 4: Monitoring parsing progress${NC}"
echo "Waiting for parsing to complete..."
echo ""

MAX_WAIT=60  # 60 seconds
WAIT_TIME=0
LAST_STATUS=""

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    RUN_DETAILS=$(curl -s "$API_URL/v1/runs/$RUN_ID")
    CURRENT_STATUS=$(echo "$RUN_DETAILS" | jq -r '.status')
    
    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ]; then
        echo "Status: $CURRENT_STATUS"
        LAST_STATUS="$CURRENT_STATUS"
    fi
    
    if [ "$CURRENT_STATUS" = "complete" ]; then
        echo -e "${GREEN}✓ Parsing complete!${NC}"
        break
    elif [ "$CURRENT_STATUS" = "failed" ]; then
        echo -e "${YELLOW}✗ Parsing failed${NC}"
        NOTES=$(echo "$RUN_DETAILS" | jq -r '.notes // "No error details available"')
        echo "Error: $NOTES"
        exit 1
    fi
    
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
    echo -n "."
done

echo ""
echo ""

if [ "$CURRENT_STATUS" != "complete" ]; then
    echo -e "${YELLOW}⚠ Parsing still in progress after ${MAX_WAIT}s${NC}"
    echo "The task is running in the background."
    echo "Check status with: curl $API_URL/v1/runs/$RUN_ID"
    exit 0
fi

echo -e "${BLUE}Step 5: Viewing results${NC}"
echo ""

RUN_DETAILS=$(curl -s "$API_URL/v1/runs/$RUN_ID")
echo "$RUN_DETAILS" | jq '{
    id: .id,
    type: .type,
    label: .label,
    status: .status,
    created_at: .created_at
}'

echo ""
echo -e "${GREEN}=========================================="
echo "  Demo Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  - View run details: curl $API_URL/v1/runs/$RUN_ID | jq ."
echo "  - List all runs: curl $API_URL/v1/runs | jq ."
echo "  - Check worker health: curl $API_URL/v1/worker/health | jq ."
echo "  - View worker logs: docker compose logs -f worker"
echo ""
