#!/bin/bash
# Master script for executing the GCP migration
# This script runs all necessary fixes and deployment steps in sequence

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default configuration
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
SERVICE="admin-api"
SOURCE_DIR="services/admin-api"
MIN_INSTANCES=0
MAX_INSTANCES=5
SKIP_PERMISSIONS=false
SKIP_DEPLOY=false
RUN_VERIFICATION=true

# Banner
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║             AI Orchestra GCP Migration Executor                ║"
echo "║                All-in-One Migration Solution                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --source-dir)
      SOURCE_DIR="$2"
      shift 2
      ;;
    --min-instances)
      MIN_INSTANCES="$2"
      shift 2
      ;;
    --max-instances)
      MAX_INSTANCES="$2"
      shift 2
      ;;
    --skip-permissions)
      SKIP_PERMISSIONS=true
      shift
      ;;
    --skip-deploy)
      SKIP_DEPLOY=true
      shift
      ;;
    --no-verification)
      RUN_VERIFICATION=false
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --project-id ID       GCP project ID (default: cherry-ai-project)"
      echo "  --region REGION       GCP region (default: us-central1)"
      echo "  --service NAME        Service name (default: admin-api)"
      echo "  --source-dir DIR      Source directory (default: services/admin-api)"
      echo "  --min-instances N     Minimum instances (default: 0)"
      echo "  --max-instances N     Maximum instances (default: 5)"
      echo "  --skip-permissions    Skip fixing service account permissions"
      echo "  --skip-deploy         Skip deployment step"
      echo "  --no-verification     Skip verification step"
      echo "  --help                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Function to check if a file exists
file_exists() {
  if [ -f "$1" ]; then
    return 0
  else
    return 1
  fi
}

# Function to check if a command exists
command_exists() {
  if command -v "$1" &> /dev/null; then
    return 0
  else
    return 1
  fi
}

# 1. Verify prerequisites
echo -e "\n${YELLOW}${BOLD}STEP 1: Checking prerequisites...${NC}"

# Check if gcloud is installed
if ! command_exists "gcloud"; then
  echo -e "${RED}Error: gcloud CLI is not installed but is required.${NC}"
  echo "Please install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Check if poetry is installed
if ! command_exists "poetry"; then
  echo -e "${RED}Error: poetry is not installed but is required.${NC}"
  echo "Please install Poetry: https://python-poetry.org/docs/#installation"
  exit 1
fi

# Check if docker is installed
if ! command_exists "docker"; then
  echo -e "${RED}Error: docker is not installed but is required.${NC}"
  echo "Please install Docker: https://docs.docker.com/get-docker/"
  exit 1
fi

echo -e "${GREEN}✓ All required tools are installed${NC}"

# 2. Fix Poetry configuration
echo -e "\n${YELLOW}${BOLD}STEP 2: Verifying Poetry configuration...${NC}"

# Check if pyproject.toml exists
if ! file_exists "${SOURCE_DIR}/pyproject.toml"; then
  echo -e "${RED}Error: ${SOURCE_DIR}/pyproject.toml does not exist${NC}"
  exit 1
fi

# Check if pyproject.toml has [tool.poetry] section
if ! grep -q "\[tool.poetry\]" "${SOURCE_DIR}/pyproject.toml"; then
  echo -e "${YELLOW}Warning: pyproject.toml does not have [tool.poetry] section. Fixing...${NC}"
  
  # Create a backup of the original file
  cp "${SOURCE_DIR}/pyproject.toml" "${SOURCE_DIR}/pyproject.toml.backup"
  echo -e "${BLUE}Created backup at ${SOURCE_DIR}/pyproject.toml.backup${NC}"
  
  # Convert [project] to [tool.poetry] if it exists
  if grep -q "\[project\]" "${SOURCE_DIR}/pyproject.toml"; then
    sed -i 's/\[project\]/\[tool.poetry\]/g' "${SOURCE_DIR}/pyproject.toml"
    echo -e "${GREEN}✓ Converted [project] to [tool.poetry] in pyproject.toml${NC}"
  else
    echo -e "${RED}Error: pyproject.toml does not have [project] section to convert${NC}"
    echo "Please fix pyproject.toml manually and refer to the migration guide."
    exit 1
  fi
else
  echo -e "${GREEN}✓ pyproject.toml already has correct Poetry format${NC}"
fi

# 3. Fix service account permissions
if [ "$SKIP_PERMISSIONS" = false ]; then
  echo -e "\n${YELLOW}${BOLD}STEP 3: Fixing service account permissions...${NC}"
  
  if file_exists "fix_service_account_permissions.sh"; then
    chmod +x fix_service_account_permissions.sh
    ./fix_service_account_permissions.sh
    if [ $? -ne 0 ]; then
      echo -e "${RED}Error: Failed to fix service account permissions${NC}"
      exit 1
    fi
  else
    echo -e "${RED}Error: fix_service_account_permissions.sh not found${NC}"
    echo "Please run this script from the project root directory."
    exit 1
  fi
else
  echo -e "\n${YELLOW}${BOLD}STEP 3: Skipping service account permissions (--skip-permissions specified)${NC}"
fi

# 4. Deploy to GCP
if [ "$SKIP_DEPLOY" = false ]; then
  echo -e "\n${YELLOW}${BOLD}STEP 4: Deploying to GCP...${NC}"
  
  if file_exists "deploy_to_gcp.sh"; then
    chmod +x deploy_to_gcp.sh
    ./deploy_to_gcp.sh \
      --project-id "${PROJECT_ID}" \
      --region "${REGION}" \
      --service "${SERVICE}" \
      --source-dir "${SOURCE_DIR}" \
      --min-instances "${MIN_INSTANCES}" \
      --max-instances "${MAX_INSTANCES}"
    
    if [ $? -ne 0 ]; then
      echo -e "${RED}Error: Deployment failed${NC}"
      exit 1
    fi
  else
    echo -e "${RED}Error: deploy_to_gcp.sh not found${NC}"
    echo "Please run this script from the project root directory."
    exit 1
  fi
else
  echo -e "\n${YELLOW}${BOLD}STEP 4: Skipping deployment (--skip-deploy specified)${NC}"
fi

# 5. Verify migration success
if [ "$RUN_VERIFICATION" = true ]; then
  echo -e "\n${YELLOW}${BOLD}STEP 5: Verifying migration success...${NC}"
  
  # Skip verification if deployment was skipped
  if [ "$SKIP_DEPLOY" = true ]; then
    echo -e "${YELLOW}Skipping verification because deployment was skipped.${NC}"
    echo -e "${YELLOW}To verify the deployment, please run the script without the --skip-deploy flag.${NC}"
    # Set default values for summary
    HTTP_STATUS="skipped"
    ERROR_COUNT=0
  else
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "${SERVICE}" \
      --platform=managed \
      --region="${REGION}" \
      --format="value(status.url)" \
      --project="${PROJECT_ID}" 2>/dev/null)
    
    if [ -z "$SERVICE_URL" ]; then
      echo -e "${RED}Error: Could not find service ${SERVICE} in project ${PROJECT_ID}, region ${REGION}${NC}"
      echo -e "${YELLOW}Service may not have been deployed yet.${NC}"
      # Set default values for summary
      HTTP_STATUS="not_found"
      ERROR_COUNT=0
    else
      echo "Service URL: ${SERVICE_URL}"
      
      # Check if the service is responding
      HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}" || echo "error")
      
      if [ "$HTTP_STATUS" = "200" ]; then
        echo -e "${GREEN}✓ Service is up and responding with HTTP 200${NC}"
      elif [ "$HTTP_STATUS" = "error" ]; then
        echo -e "${RED}Error: Could not connect to the service${NC}"
        echo "Please check the service logs for more information."
      else
        echo -e "${YELLOW}Warning: Service returned HTTP ${HTTP_STATUS}${NC}"
        echo "This may indicate an issue with the service."
      fi
      
      # Check the service logs for errors
      echo -e "\nChecking service logs for errors..."
      ERROR_COUNT=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE} AND severity>=ERROR" \
        --limit=10 \
        --format="value(textPayload)" \
        --project="${PROJECT_ID}" 2>/dev/null | wc -l)
      
      if [ $ERROR_COUNT -eq 0 ]; then
        echo -e "${GREEN}✓ No errors found in recent logs${NC}"
      else
        echo -e "${YELLOW}Warning: Found ${ERROR_COUNT} error entries in recent logs${NC}"
        echo "Please check the logs for more information:"
        echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE} AND severity>=ERROR\" --project=${PROJECT_ID}"
      fi
    fi
  fi
else
  echo -e "\n${YELLOW}${BOLD}STEP 5: Skipping verification (--no-verification specified)${NC}"
fi

# 6. Migration summary
echo -e "\n${BLUE}${BOLD}Migration Summary:${NC}"
echo -e "  Poetry Configuration: ${GREEN}Fixed✓${NC}"
if [ "$SKIP_PERMISSIONS" = false ]; then
  echo -e "  Service Account Permissions: ${GREEN}Fixed✓${NC}"
else
  echo -e "  Service Account Permissions: ${YELLOW}Skipped${NC}"
fi
if [ "$SKIP_DEPLOY" = false ]; then
  echo -e "  Deployment: ${GREEN}Completed✓${NC}"
else
  echo -e "  Deployment: ${YELLOW}Skipped${NC}"
fi
if [ "$RUN_VERIFICATION" = true ]; then
  if [ "$HTTP_STATUS" = "200" ] && [ $ERROR_COUNT -eq 0 ]; then
    echo -e "  Verification: ${GREEN}Successful✓${NC}"
  else
    echo -e "  Verification: ${YELLOW}Warnings detected${NC}"
  fi
else
  echo -e "  Verification: ${YELLOW}Skipped${NC}"
fi

echo -e "\n${GREEN}${BOLD}Migration process completed!${NC}"
echo -e "For more details, please refer to GCP_MIGRATION_GUIDE.md"