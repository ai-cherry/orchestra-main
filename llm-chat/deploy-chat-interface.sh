#!/bin/bash
# Script to deploy the LLM chat interface to Google Cloud Storage as a static website
# This provides a quick production environment for testing your LLM strategy

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
BUCKET_NAME=""
DOMAIN_NAME=""

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --bucket)
      BUCKET_NAME="$2"
      shift 2
      ;;
    --domain)
      DOMAIN_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Usage: $0 --project=PROJECT_ID [--bucket=BUCKET_NAME] [--domain=DOMAIN_NAME] [--region=REGION]"
      exit 1
      ;;
  esac
done

# Validate inputs
if [ -z "$PROJECT_ID" ]; then
  echo -e "${RED}Error: Project ID is required${NC}"
  echo "Please specify with --project or set default project with: gcloud config set project PROJECT_ID"
  exit 1
fi

# If bucket name is not provided, create a default one
if [ -z "$BUCKET_NAME" ]; then
  BUCKET_NAME="${PROJECT_ID}-llm-chat"
  echo -e "${YELLOW}No bucket name specified. Using default: $BUCKET_NAME${NC}"
fi

echo -e "${BLUE}=== Deploying LLM Chat Interface ===${NC}"
echo -e "Project: ${GREEN}$PROJECT_ID${NC}"
echo -e "Bucket: ${GREEN}$BUCKET_NAME${NC}"
echo -e "Region: ${GREEN}$REGION${NC}"
if [ ! -z "$DOMAIN_NAME" ]; then
  echo -e "Domain: ${GREEN}$DOMAIN_NAME${NC}"
fi

# Check if user is authenticated with GCP
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
  echo -e "${RED}Error: Not authenticated with Google Cloud SDK${NC}"
  echo "Please run: gcloud auth login"
  exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID"

# Check if the bucket exists, create if it doesn't
if ! gsutil ls -b "gs://${BUCKET_NAME}" &> /dev/null; then
  echo -e "${YELLOW}Bucket does not exist. Creating bucket...${NC}"
  gsutil mb -l "$REGION" "gs://${BUCKET_NAME}"
else
  echo -e "${GREEN}Bucket already exists.${NC}"
fi

# Configure bucket for website hosting
echo -e "${BLUE}Configuring bucket for website hosting...${NC}"
gsutil web set -m index.html "gs://${BUCKET_NAME}"

# Make bucket publicly readable
echo -e "${BLUE}Making bucket publicly readable...${NC}"
gsutil iam ch allUsers:objectViewer "gs://${BUCKET_NAME}"

# Update the API endpoint in the HTML file if provided
if [ ! -z "$API_ENDPOINT" ]; then
  echo -e "${BLUE}Updating API endpoint in the HTML file...${NC}"
  sed -i "s|const API_ENDPOINT = \".*\"|const API_ENDPOINT = \"$API_ENDPOINT\"|g" "index.html"
fi

# Upload the HTML file to the bucket
echo -e "${BLUE}Uploading files to bucket...${NC}"
gsutil -h "Cache-Control:public, max-age=3600" cp index.html "gs://${BUCKET_NAME}/"

# If a domain is provided, set up HTTPS with Cloud CDN
if [ ! -z "$DOMAIN_NAME" ]; then
  echo -e "${BLUE}Setting up HTTPS with Cloud CDN...${NC}"
  
  # Create a load balancer with HTTPS
  BACKEND_NAME="${BUCKET_NAME}-backend"
  
  # Check if the required APIs are enabled
  if ! gcloud services list --enabled --filter="name:compute.googleapis.com" | grep compute.googleapis.com; then
    echo -e "${YELLOW}Enabling Compute API...${NC}"
    gcloud services enable compute.googleapis.com
  fi
  
  # Create backend bucket
  echo -e "${BLUE}Creating backend bucket...${NC}"
  gcloud compute backend-buckets create "$BACKEND_NAME" \
    --gcs-bucket-name="$BUCKET_NAME" \
    --enable-cdn
  
  # Create URL map
  URL_MAP_NAME="${BUCKET_NAME}-url-map"
  echo -e "${BLUE}Creating URL map...${NC}"
  gcloud compute url-maps create "$URL_MAP_NAME" \
    --default-backend-bucket="$BACKEND_NAME"
  
  # Create HTTP proxy
  HTTP_PROXY_NAME="${BUCKET_NAME}-http-proxy"
  echo -e "${BLUE}Creating HTTP proxy...${NC}"
  gcloud compute target-http-proxies create "$HTTP_PROXY_NAME" \
    --url-map="$URL_MAP_NAME"
  
  # Create forwarding rule
  FORWARDING_RULE_NAME="${BUCKET_NAME}-http-rule"
  echo -e "${BLUE}Creating forwarding rule...${NC}"
  gcloud compute forwarding-rules create "$FORWARDING_RULE_NAME" \
    --global \
    --target-http-proxy="$HTTP_PROXY_NAME" \
    --ports=80
  
  echo -e "${YELLOW}Note: For HTTPS setup with custom domain, you'll need to:${NC}"
  echo -e "1. Create an SSL certificate (gcloud compute ssl-certificates create)"
  echo -e "2. Create an HTTPS proxy with the certificate"
  echo -e "3. Add a forwarding rule for port 443"
  echo -e "4. Update your domain's DNS to point to the load balancer IP"
  echo -e "See: https://cloud.google.com/load-balancing/docs/https/ext-https-lb-simple"
fi

# Get the public URL
if [ -z "$DOMAIN_NAME" ]; then
  PUBLIC_URL="https://storage.googleapis.com/${BUCKET_NAME}/index.html"
else
  PUBLIC_URL="http://${DOMAIN_NAME}/"
fi

echo -e "\n${GREEN}=== Deployment Complete! ===${NC}"
echo -e "LLM Chat interface is now live at: ${GREEN}$PUBLIC_URL${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "1. Test the interface and make sure it's working correctly"
echo -e "2. Connect to your preferred LLM API by uncommenting and modifying the API call in the JavaScript code"
echo -e "3. For production use, set up proper authentication and API key management"

if [ -z "$DOMAIN_NAME" ]; then
  echo -e "4. For a custom domain, redeploy with --domain=your-domain.com"
fi

echo -e "\n${BLUE}=== Deployment Successful ===${NC}"
