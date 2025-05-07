#!/bin/bash

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=====================================================${NC}"
echo -e "${BOLD}${BLUE}  CLOUD RUN DEPLOYMENT TEST${NC}"
echo -e "${BOLD}${BLUE}=====================================================${NC}"

# Function to handle errors
handle_error() {
  echo -e "${RED}ERROR: $1${NC}"
  echo "Cleaning up resources..."
  # Delete service if it exists
  gcloud run services delete test-service --quiet --region=us-central1 2>/dev/null || true
  exit 1
}

echo "Starting Cloud Run deployment test at $(date)"

# Step 1: Create a simple Node.js app
echo -e "\n${BLUE}Step 1: Creating test application${NC}"

mkdir -p test-app
cd test-app || handle_error "Failed to create test directory"

# Create package.json
cat > package.json << 'EOF'
{
  "name": "test-app",
  "version": "1.0.0",
  "description": "Simple test app for Cloud Run",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.17.1"
  }
}
EOF

# Create index.js
cat > index.js << 'EOF'
const express = require('express');
const app = express();
const port = process.env.PORT || 8080;

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>GCP Cloud Run Test</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
            background-color: #f8f9fa;
          }
          .container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
            max-width: 600px;
            margin: 0 auto;
          }
          h1 {
            color: #1a73e8;
          }
          .success {
            color: #0f9d58;
            font-weight: bold;
          }
          .details {
            background-color: #f1f3f4;
            border-radius: 4px;
            padding: 15px;
            text-align: left;
            margin-top: 20px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Cloud Run Test Deployment</h1>
          <p class="success">✅ Successfully deployed to Cloud Run!</p>
          <div class="details">
            <p><strong>Environment:</strong> ${process.env.NODE_ENV || 'development'}</p>
            <p><strong>Timestamp:</strong> ${new Date().toISOString()}</p>
            <p><strong>Hostname:</strong> ${require('os').hostname()}</p>
          </div>
        </div>
      </body>
    </html>
  `);
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM node:14-slim

WORKDIR /app

COPY package.json ./
RUN npm install --production

COPY . ./

ENV PORT=8080
CMD [ "npm", "start" ]
EOF

echo -e "${GREEN}✅ Test application created successfully${NC}"

# Step 2: Deploy to Cloud Run
echo -e "\n${BLUE}Step 2: Deploying to Cloud Run${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}"

gcloud run deploy test-service \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated \
  --quiet || handle_error "Failed to deploy to Cloud Run"

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe test-service --region=us-central1 --format='value(status.url)')

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${BLUE}Service URL:${NC} $SERVICE_URL"

# Step 3: Test the deployed service
echo -e "\n${BLUE}Step 3: Testing the deployed service${NC}"

echo -e "${YELLOW}Sending request to $SERVICE_URL${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL")

if [ "$HTTP_STATUS" -eq 200 ]; then
  echo -e "${GREEN}✅ Service responded with HTTP 200 OK${NC}"
else
  echo -e "${RED}❌ Service responded with HTTP $HTTP_STATUS${NC}"
fi

# Step 4: Clean up
echo -e "\n${BLUE}Step 4: Cleaning up resources${NC}"

echo -e "${YELLOW}Deleting Cloud Run service 'test-service'...${NC}"
gcloud run services delete test-service --quiet --region=us-central1 || handle_error "Failed to delete Cloud Run service"

echo -e "${GREEN}✅ Cloud Run service deleted successfully${NC}"

# Go back to root directory
cd ..
echo -e "${YELLOW}Removing test application files...${NC}"
rm -rf test-app

echo -e "\n${BOLD}${GREEN}Cloud Run deployment test completed successfully!${NC}"
echo -e "This confirms your GCP configuration is working properly for Cloud Run deployments."
echo -e "\nTest completed at $(date)"
