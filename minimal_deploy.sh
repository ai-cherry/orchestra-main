#!/bin/bash
# Minimal Cloud Run Deployment Script
# This script focuses only on deploying to Cloud Run using existing credentials

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║             MINIMAL CLOUD RUN DEPLOYMENT                      ║"
echo "║                 USING EXISTING CREDENTIALS                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Create service account file (if embedded JSON is available)
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
    echo -e "${GREEN}Using GCP_MASTER_SERVICE_JSON${NC}"
    echo "$GCP_MASTER_SERVICE_JSON" > key.json
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
elif [ -n "$GCP_PROJECT_MANAGEMENT_KEY" ]; then
    echo -e "${GREEN}Using GCP_PROJECT_MANAGEMENT_KEY${NC}"
    echo "$GCP_PROJECT_MANAGEMENT_KEY" > key.json
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
fi

# Authenticate with gcloud (if needed)
if [ -f "$(pwd)/key.json" ]; then
    echo -e "${YELLOW}Activating service account...${NC}"
    gcloud auth activate-service-account --key-file="$(pwd)/key.json"
fi

# Set project and region
echo -e "${YELLOW}Setting project and region...${NC}"
gcloud config set project "$GCP_PROJECT_ID"
gcloud config set compute/region "$GCP_REGION"

# Verify authentication
echo -e "${YELLOW}Verifying authentication...${NC}"
gcloud auth list

# Create simple Dockerfile if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo -e "${YELLOW}Creating Dockerfile...${NC}"
    cat <<EOF > Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Configure the container
ENV PORT=8080
EXPOSE \${PORT}

# Run the web service
CMD exec gunicorn --bind :\${PORT} --workers 1 --threads 8 --timeout 0 app:app
EOF
fi

# Create simple app code if it doesn't exist
if [ ! -f app.py ]; then
    echo -e "${YELLOW}Creating sample app.py...${NC}"
    cat <<EOF > app.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "AI Orchestra deployed on Cloud Run"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
EOF
fi

# Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo -e "${YELLOW}Creating requirements.txt...${NC}"
    cat <<EOF > requirements.txt
flask==2.0.1
gunicorn==20.1.0
EOF
fi

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Build and deploy to Cloud Run
echo -e "${YELLOW}Building and deploying to Cloud Run...${NC}"
gcloud builds submit --tag "gcr.io/$GCP_PROJECT_ID/orchestra-app"

echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy orchestra-app \
    --image "gcr.io/$GCP_PROJECT_ID/orchestra-app" \
    --platform managed \
    --region "$GCP_REGION" \
    --allow-unauthenticated

# Get the deployed URL
SERVICE_URL=$(gcloud run services describe orchestra-app --platform managed --region "$GCP_REGION" --format 'value(status.url)')

# Clean up credentials
if [ -f "$(pwd)/key.json" ]; then
    echo -e "${YELLOW}Cleaning up credentials...${NC}"
    rm "$(pwd)/key.json"
fi

echo -e "\n${GREEN}${BOLD}DEPLOYMENT COMPLETE!${NC}"
echo -e "Your application is now deployed to Google Cloud Run!"
echo -e "\nYou can view your deployed application at:"
echo -e "${BLUE}$SERVICE_URL${NC}"

echo -e "\n${GREEN}${BOLD}AI Orchestra is now running in Google Cloud Platform!${NC}"
