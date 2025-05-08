#!/bin/bash
# validate_deployment.sh - Validate the deployment of the Orchestra application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
ENV="dev"

# Handle errors
handle_error() {
  echo -e "${RED}Error occurred at line $1${NC}"
  exit 1
}

trap 'handle_error $LINENO' ERR

# Print banner
echo -e "${GREEN}"
echo "=================================================="
echo "   Orchestra Deployment Validation"
echo "=================================================="
echo -e "${NC}"

# Check if service URL is provided
if [ -z "$1" ]; then
  echo -e "${YELLOW}No service URL provided, attempting to get it from Cloud Run${NC}"
  
  # Check if gcloud is authenticated
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
    echo -e "${RED}Not authenticated with gcloud. Please run 'gcloud auth login' or provide the service URL as an argument.${NC}"
    exit 1
  fi
  
  # Get service URL from Cloud Run
  SERVICE_URL=$(gcloud run services describe orchestra-api --platform managed --region "$REGION" --format="value(status.url)" 2>/dev/null || echo "")
  
  if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}Could not retrieve service URL. Please provide it as an argument.${NC}"
    exit 1
  fi
else
  SERVICE_URL="$1"
fi

echo -e "${YELLOW}Validating deployment at: ${SERVICE_URL}${NC}"

# Test 1: Check if the service is responding
echo -e "${YELLOW}Test 1: Checking if service is responding...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL" | grep -q "200"; then
  echo -e "${GREEN}✓ Service is responding${NC}"
else
  echo -e "${RED}✗ Service is not responding${NC}"
  exit 1
fi

# Test 2: Check health endpoint
echo -e "${YELLOW}Test 2: Checking health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s "${SERVICE_URL}/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
  echo -e "${GREEN}✓ Health check passed${NC}"
else
  echo -e "${RED}✗ Health check failed${NC}"
  echo "Response: $HEALTH_RESPONSE"
  exit 1
fi

# Test 3: Check metrics endpoint
echo -e "${YELLOW}Test 3: Checking metrics endpoint...${NC}"
METRICS_RESPONSE=$(curl -s "${SERVICE_URL}/metrics")
if echo "$METRICS_RESPONSE" | grep -q "success"; then
  echo -e "${GREEN}✓ Metrics endpoint is working${NC}"
else
  echo -e "${RED}✗ Metrics endpoint failed${NC}"
  echo "Response: $METRICS_RESPONSE"
  exit 1
fi

# Test 4: Test memory operations
echo -e "${YELLOW}Test 4: Testing memory operations...${NC}"

# Generate a unique test key
TEST_KEY="test_$(date +%s)"

# Store data
echo -e "${YELLOW}  4.1: Storing test data...${NC}"
STORE_RESPONSE=$(curl -s -X POST "${SERVICE_URL}/memory/${TEST_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"content":{"test":"data","timestamp":"'"$(date)"'"}}')

if echo "$STORE_RESPONSE" | grep -q "success"; then
  echo -e "${GREEN}    ✓ Data stored successfully${NC}"
else
  echo -e "${RED}    ✗ Failed to store data${NC}"
  echo "    Response: $STORE_RESPONSE"
  exit 1
fi

# Retrieve data
echo -e "${YELLOW}  4.2: Retrieving test data...${NC}"
RETRIEVE_RESPONSE=$(curl -s "${SERVICE_URL}/memory/${TEST_KEY}")

if echo "$RETRIEVE_RESPONSE" | grep -q "found.*true"; then
  echo -e "${GREEN}    ✓ Data retrieved successfully${NC}"
else
  echo -e "${RED}    ✗ Failed to retrieve data${NC}"
  echo "    Response: $RETRIEVE_RESPONSE"
  exit 1
fi

# Delete data
echo -e "${YELLOW}  4.3: Deleting test data...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE "${SERVICE_URL}/memory/${TEST_KEY}")

if echo "$DELETE_RESPONSE" | grep -q "success.*true"; then
  echo -e "${GREEN}    ✓ Data deleted successfully${NC}"
else
  echo -e "${RED}    ✗ Failed to delete data${NC}"
  echo "    Response: $DELETE_RESPONSE"
  exit 1
fi

# Test 5: Check search functionality
echo -e "${YELLOW}Test 5: Testing search functionality...${NC}"

# Store data for search
SEARCH_KEY="search_$(date +%s)"
curl -s -X POST "${SERVICE_URL}/memory/${SEARCH_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"content":{"searchable":"This is a unique search term for validation"}}' > /dev/null

# Search for the data
SEARCH_RESPONSE=$(curl -s "${SERVICE_URL}/memory/search?query=unique+search+term")

if echo "$SEARCH_RESPONSE" | grep -q "success.*true"; then
  echo -e "${GREEN}✓ Search functionality is working${NC}"
else
  echo -e "${RED}✗ Search functionality failed${NC}"
  echo "Response: $SEARCH_RESPONSE"
  exit 1
fi

# Clean up search test data
curl -s -X DELETE "${SERVICE_URL}/memory/${SEARCH_KEY}" > /dev/null

echo -e "${GREEN}"
echo "=================================================="
echo "   Validation Complete - All Tests Passed!"
echo "=================================================="
echo -e "${NC}"
echo -e "Service URL: ${GREEN}${SERVICE_URL}${NC}"