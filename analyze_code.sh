#!/bin/bash
# analyze_code.sh - Script for running Gemini-powered code analysis

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Default values
PROJECT_ID="agi-baby-cherry"
SECRET_NAME="GEMINI_API_KEY"
ANALYSIS_TYPE="security"
OUTPUT_FILE="analysis-results.json"
ENDPOINT="https://us-central1-agi-baby-cherry.cloudfunctions.net/code-analysis"

# Function to display usage information
usage() {
  echo -e "${BOLD}Usage:${NC} $0 [OPTIONS] FILES"
  echo
  echo -e "${BOLD}Arguments:${NC}"
  echo "  FILES               Comma-separated list of files to analyze (required)"
  echo
  echo -e "${BOLD}Options:${NC}"
  echo "  --project=ID        GCP Project ID (default: $PROJECT_ID)"
  echo "  --secret=NAME       API key secret name (default: $SECRET_NAME)"
  echo "  --type=TYPE         Analysis type: security|performance|style (default: $ANALYSIS_TYPE)"
  echo "  --output=PATH       Path to output file (default: $OUTPUT_FILE)"
  echo "  --endpoint=URL      Code analysis endpoint URL (default: $ENDPOINT)"
  echo "  --use-key=KEY       Directly use API key instead of fetching from Secret Manager"
  echo "  --help              Display this help message"
  echo
  echo -e "${BOLD}Example:${NC}"
  echo "  $0 orchestrator/main.py,core/utils.py"
  echo "  $0 --type=performance 'orchestrator/*.py'"
}

# Process command-line arguments
FILES=""

for arg in "$@"; do
  case $arg in
    --project=*)
      PROJECT_ID="${arg#*=}"
      shift
      ;;
    --secret=*)
      SECRET_NAME="${arg#*=}"
      shift
      ;;
    --type=*)
      ANALYSIS_TYPE="${arg#*=}"
      shift
      ;;
    --output=*)
      OUTPUT_FILE="${arg#*=}"
      shift
      ;;
    --endpoint=*)
      ENDPOINT="${arg#*=}"
      shift
      ;;
    --use-key=*)
      API_KEY="${arg#*=}"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    --*)
      echo -e "${RED}Error: Unknown option: $arg${NC}"
      usage
      exit 1
      ;;
    *)
      if [ -z "$FILES" ]; then
        FILES="$arg"
      else
        echo -e "${RED}Error: Too many arguments.${NC}"
        usage
        exit 1
      fi
      ;;
  esac
done

# Validate required arguments
if [ -z "$FILES" ]; then
  echo -e "${RED}Error: No files specified for analysis${NC}"
  usage
  exit 1
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${BOLD}Gemini Code Analysis${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}Project:${NC} $PROJECT_ID"
echo -e "${YELLOW}Files:${NC} $FILES"
echo -e "${YELLOW}Analysis Type:${NC} $ANALYSIS_TYPE"
echo -e "${YELLOW}Output:${NC} $OUTPUT_FILE"
echo -e "${BLUE}======================================================${NC}"

# Get API key if not provided directly
if [ -z "$API_KEY" ]; then
  echo -e "${YELLOW}Fetching API key from Secret Manager...${NC}"
  
  # Check if gcloud is installed
  if ! command -v gcloud &>/dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed or not in PATH${NC}"
    echo -e "Please install the Google Cloud SDK and try again."
    exit 1
  fi

  # Check if user is authenticated with gcloud
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo -e "${RED}Error: Not authenticated with gcloud${NC}"
    echo -e "Please run 'gcloud auth login' and try again."
    exit 1
  fi

  # Fetch the API key from Secret Manager
  API_KEY=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null)
  
  if [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: Failed to retrieve API key from Secret Manager${NC}"
    echo -e "Please check that the secret $SECRET_NAME exists and you have access."
    exit 1
  fi
  
  echo -e "${GREEN}API key retrieved successfully${NC}"
else
  echo -e "${YELLOW}Using provided API key${NC}"
fi

# Prepare the JSON payload
# Note: This is a simple approach. For complex file patterns, consider using jq
formatted_files=$(echo "$FILES" | sed 's/,/","/g')
PAYLOAD='{
  "files": ["'"$formatted_files"'"],
  "analysis_type": "'"$ANALYSIS_TYPE"'"
}'

echo -e "${YELLOW}Sending request to code analysis endpoint...${NC}"
echo -e "${BLUE}Endpoint:${NC} $ENDPOINT"

# Call the API and save the response
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

CURL_EXIT_CODE=$?

if [ $CURL_EXIT_CODE -ne 0 ]; then
  echo -e "${RED}Error: Failed to connect to the endpoint (curl exit code: $CURL_EXIT_CODE)${NC}"
  exit 1
fi

# Check if the response is empty or contains an error
if [ -z "$RESPONSE" ]; then
  echo -e "${RED}Error: Empty response from the API${NC}"
  exit 1
elif echo "$RESPONSE" | grep -q "error" || echo "$RESPONSE" | grep -q "Error"; then
  echo -e "${RED}API Error:${NC}"
  echo "$RESPONSE"
  exit 1
fi

# Save the response to the output file
echo "$RESPONSE" > "$OUTPUT_FILE"

echo -e "${GREEN}Analysis completed successfully!${NC}"
echo -e "${YELLOW}Results saved to:${NC} $OUTPUT_FILE"

# Check for issues in the analysis (this logic might need adjustment based on actual response format)
ISSUES_COUNT=$(echo "$RESPONSE" | grep -o "issue" | wc -l)

if [ "$ISSUES_COUNT" -gt 0 ]; then
  echo -e "${YELLOW}Found approximately $ISSUES_COUNT potential issues to review${NC}"
  
  # Print a preview (first 5 lines) of the results
  echo -e "${BLUE}Preview of analysis results:${NC}"
  echo "$RESPONSE" | head -n 5
  echo -e "${YELLOW}...(See $OUTPUT_FILE for complete results)${NC}"
else
  echo -e "${GREEN}No immediate issues found in the analysis${NC}"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}${BOLD}Code analysis completed!${NC}"
echo -e "${BLUE}======================================================${NC}"
