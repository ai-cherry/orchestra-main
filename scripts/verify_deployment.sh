#!/bin/bash
# Deployment Verification Script for AI Orchestra
# This script verifies that all components are working correctly after deployment

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
SERVICE_NAME="orchestra-api"
ENVIRONMENT=${1:-"dev"}  # Default to dev environment if not specified

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Set service name based on environment
if [ "$ENVIRONMENT" == "prod" ]; then
  SERVICE_NAME="orchestra-prod"
elif [ "$ENVIRONMENT" == "staging" ]; then
  SERVICE_NAME="orchestra-staging"
else
  SERVICE_NAME="orchestra-dev"
fi

echo -e "${GREEN}Verifying deployment of AI Orchestra in ${ENVIRONMENT} environment...${NC}"

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if required tools are installed
echo -e "${YELLOW}Checking required tools...${NC}"
MISSING_TOOLS=0

if ! command_exists gcloud; then
  echo -e "${RED}gcloud CLI is not installed. Please install it from https://cloud.google.com/sdk/docs/install${NC}"
  MISSING_TOOLS=1
fi

if ! command_exists curl; then
  echo -e "${RED}curl is not installed. Please install it using your package manager.${NC}"
  MISSING_TOOLS=1
fi

if ! command_exists jq; then
  echo -e "${RED}jq is not installed. Please install it using your package manager.${NC}"
  MISSING_TOOLS=1
fi

if [ $MISSING_TOOLS -eq 1 ]; then
  echo -e "${RED}Please install the missing tools and try again.${NC}"
  exit 1
fi

echo -e "${GREEN}All required tools are installed.${NC}"

# Check if user is authenticated with gcloud
echo -e "${YELLOW}Checking gcloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
  echo -e "${RED}You are not authenticated with gcloud. Please run 'gcloud auth login' first.${NC}"
  exit 1
fi

echo -e "${GREEN}gcloud authentication verified.${NC}"

# Check if the project exists and user has access
echo -e "${YELLOW}Checking project access...${NC}"
if ! gcloud projects describe ${PROJECT_ID} >/dev/null 2>&1; then
  echo -e "${RED}Project ${PROJECT_ID} does not exist or you don't have access to it.${NC}"
  exit 1
fi

echo -e "${GREEN}Project access verified.${NC}"

# Check if the Cloud Run service exists
echo -e "${YELLOW}Checking Cloud Run service...${NC}"
if ! gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} >/dev/null 2>&1; then
  echo -e "${RED}Cloud Run service ${SERVICE_NAME} does not exist in region ${REGION}.${NC}"
  exit 1
fi

echo -e "${GREEN}Cloud Run service exists.${NC}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --format="value(status.url)")
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"

# Check if the service is responding
echo -e "${YELLOW}Checking if service is responding...${NC}"
if ! curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL}/health | grep -q "200"; then
  echo -e "${RED}Service is not responding correctly. HTTP status code is not 200.${NC}"
  echo -e "${YELLOW}Response from ${SERVICE_URL}/health:${NC}"
  curl -s ${SERVICE_URL}/health
  echo ""
  exit 1
fi

echo -e "${GREEN}Service is responding correctly.${NC}"

# Check Redis connection
echo -e "${YELLOW}Checking Redis connection...${NC}"
REDIS_CHECK=$(curl -s ${SERVICE_URL}/health | jq -r '.redis_status // "unknown"')
if [ "$REDIS_CHECK" != "connected" ]; then
  echo -e "${RED}Redis connection check failed. Status: ${REDIS_CHECK}${NC}"
  echo -e "${YELLOW}This may indicate issues with Redis configuration or connectivity.${NC}"
  exit 1
fi

echo -e "${GREEN}Redis connection verified.${NC}"

# Check Firestore connection
echo -e "${YELLOW}Checking Firestore connection...${NC}"
FIRESTORE_CHECK=$(curl -s ${SERVICE_URL}/health | jq -r '.firestore_status // "unknown"')
if [ "$FIRESTORE_CHECK" != "connected" ]; then
  echo -e "${RED}Firestore connection check failed. Status: ${FIRESTORE_CHECK}${NC}"
  echo -e "${YELLOW}This may indicate issues with Firestore configuration or permissions.${NC}"
  exit 1
fi

echo -e "${GREEN}Firestore connection verified.${NC}"

# Check Secret Manager access
echo -e "${YELLOW}Checking Secret Manager access...${NC}"
SECRET_CHECK=$(curl -s ${SERVICE_URL}/health | jq -r '.secret_manager_status // "unknown"')
if [ "$SECRET_CHECK" != "connected" ]; then
  echo -e "${RED}Secret Manager access check failed. Status: ${SECRET_CHECK}${NC}"
  echo -e "${YELLOW}This may indicate issues with Secret Manager configuration or permissions.${NC}"
  exit 1
fi

echo -e "${GREEN}Secret Manager access verified.${NC}"

# Check LLM API connections
echo -e "${YELLOW}Checking LLM API connections...${NC}"
LLM_CHECK=$(curl -s ${SERVICE_URL}/health | jq -r '.llm_status // "unknown"')
if [ "$LLM_CHECK" != "connected" ]; then
  echo -e "${YELLOW}LLM API connection check failed or not implemented. Status: ${LLM_CHECK}${NC}"
  echo -e "${YELLOW}This may indicate issues with LLM API keys or configuration.${NC}"
  echo -e "${YELLOW}You may need to check the logs for more details.${NC}"
else
  echo -e "${GREEN}LLM API connections verified.${NC}"
fi

# Check logs for errors
echo -e "${YELLOW}Checking logs for errors...${NC}"
ERROR_COUNT=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND severity>=ERROR" --project=${PROJECT_ID} --limit=10 --format="value(textPayload)" | wc -l)

if [ $ERROR_COUNT -gt 0 ]; then
  echo -e "${YELLOW}Found ${ERROR_COUNT} recent error logs. Here are the latest errors:${NC}"
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND severity>=ERROR" --project=${PROJECT_ID} --limit=5 --format="value(timestamp,severity,textPayload)"
  echo -e "${YELLOW}You may want to investigate these errors.${NC}"
else
  echo -e "${GREEN}No recent error logs found.${NC}"
fi

# Check resource utilization
echo -e "${YELLOW}Checking resource utilization...${NC}"
INSTANCE_COUNT=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --format="value(status.traffic.percent)")
echo -e "${GREEN}Current instance count: ${INSTANCE_COUNT}${NC}"

# Perform a simple load test
echo -e "${YELLOW}Performing a simple load test...${NC}"
echo -e "${YELLOW}Sending 10 requests to the health endpoint...${NC}"

SUCCESS_COUNT=0
for i in {1..10}; do
  if curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL}/health | grep -q "200"; then
    SUCCESS_COUNT=$((SUCCESS_COUNT+1))
  fi
  sleep 1
done

echo -e "${GREEN}Load test results: ${SUCCESS_COUNT}/10 successful requests${NC}"

if [ $SUCCESS_COUNT -lt 10 ]; then
  echo -e "${YELLOW}Not all requests were successful. This may indicate performance or stability issues.${NC}"
else
  echo -e "${GREEN}All requests were successful.${NC}"
fi

# Final verification
echo -e "\n${GREEN}Deployment Verification Summary:${NC}"
echo -e "${GREEN}✓ Cloud Run service is deployed and responding${NC}"
echo -e "${GREEN}✓ Redis connection is working${NC}"
echo -e "${GREEN}✓ Firestore connection is working${NC}"
echo -e "${GREEN}✓ Secret Manager access is working${NC}"

if [ "$LLM_CHECK" == "connected" ]; then
  echo -e "${GREEN}✓ LLM API connections are working${NC}"
else
  echo -e "${YELLOW}⚠ LLM API connections status: ${LLM_CHECK}${NC}"
fi

if [ $ERROR_COUNT -eq 0 ]; then
  echo -e "${GREEN}✓ No recent error logs found${NC}"
else
  echo -e "${YELLOW}⚠ Found ${ERROR_COUNT} recent error logs${NC}"
fi

if [ $SUCCESS_COUNT -eq 10 ]; then
  echo -e "${GREEN}✓ Load test passed with 10/10 successful requests${NC}"
else
  echo -e "${YELLOW}⚠ Load test: ${SUCCESS_COUNT}/10 successful requests${NC}"
fi

echo -e "\n${GREEN}Deployment verification completed.${NC}"

# Provide next steps
echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Monitor the application logs: gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\" --project=${PROJECT_ID} --limit=50"
echo -e "2. Set up monitoring alerts for errors and performance issues"
echo -e "3. Configure Cloud Run autoscaling based on load patterns"
echo -e "4. Implement continuous monitoring with Cloud Monitoring"