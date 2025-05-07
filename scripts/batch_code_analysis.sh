#!/bin/bash
# batch_code_analysis.sh - Script to upload staged files to GCS and trigger batch code analysis using a Cloud Function

set -eo pipefail

# Default values
PROJECT_ID="cherry-ai-project"
BUCKET_NAME="cherry-ai-project-code-analysis"
INPUT_PREFIX="input/"
FUNCTION_NAME="code_analysis"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--project) PROJECT_ID="$2"; shift ;;
    -b|--bucket) BUCKET_NAME="$2"; shift ;;
    -f|--function) FUNCTION_NAME="$2"; shift ;;
    -h|--help) 
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  -p, --project ID    GCP Project ID (default: $PROJECT_ID)"
      echo "  -b, --bucket NAME   GCS Bucket Name (default: $BUCKET_NAME)"
      echo "  -f, --function NAME Cloud Function Name (default: $FUNCTION_NAME)"
      echo "  -h, --help          Display this help message"
      exit 0
      ;;
    *) echo "Unknown parameter: $1"; exit 1 ;;
  esac
  shift
done

# Validate environment
if ! command -v gcloud &> /dev/null; then
  echo "Error: gcloud CLI not found"
  exit 1
fi

if ! command -v git &> /dev/null; then
  echo "Error: git CLI not found"
  exit 1
fi

# Get staged files
STAGED_FILES=$(git diff --cached --name-only | tr '\n' ' ')
if [ -z "$STAGED_FILES" ]; then
  echo "No staged files found to analyze."
  exit 0
fi

echo "Uploading staged files to GCS bucket: gs://$BUCKET_NAME/$INPUT_PREFIX"
# Create a temporary directory to store staged files for upload
TEMP_DIR=$(mktemp -d)
for FILE in $STAGED_FILES; do
  if [ -f "$FILE" ]; then
    cp "$FILE" "$TEMP_DIR/"
  fi
done

# Upload files to GCS
gsutil -m cp -r "$TEMP_DIR/*" "gs://$BUCKET_NAME/$INPUT_PREFIX" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "Error: Failed to upload files to GCS (details omitted for security)"
  rm -rf "$TEMP_DIR"
  exit 1
fi

rm -rf "$TEMP_DIR"
echo "Files uploaded successfully."

echo "Triggering Cloud Function for batch analysis: $FUNCTION_NAME"
# Trigger the Cloud Function with the bucket and prefix information
gcloud functions call "$FUNCTION_NAME" --data "{\"bucket\":\"$BUCKET_NAME\",\"input_prefix\":\"$INPUT_PREFIX\"}" --project="$PROJECT_ID" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "Error: Failed to trigger Cloud Function (details omitted for security)"
  exit 1
fi

echo "Batch code analysis triggered successfully. Check Cloud Function logs for results."
# Note: Results aggregation and commit blocking logic would be handled by the Cloud Function
# For now, this script assumes the function will handle notifications or further actions