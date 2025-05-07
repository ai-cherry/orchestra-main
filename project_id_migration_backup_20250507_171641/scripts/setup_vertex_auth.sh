#!/bin/bash

# Setup Script for Vertex AI and Gemini Authentication
# Project: orchestra-main
# Target Project ID: agi-baby-cherry
# Service Account: vertex-agent@agi-baby-cherry.iam.gserviceaccount.com

echo "Setting up authentication for Vertex AI and Gemini integration..."

# Step 1: Authenticate with Google Cloud SDK
echo "Authenticating with Google Cloud SDK..."
gcloud auth login
gcloud config set project agi-baby-cherry

# Step 2: Activate Service Account
echo "Activating service account vertex-agent@agi-baby-cherry.iam.gserviceaccount.com..."
# Updated to use GCP_PROJECT_MANAGEMENT_KEY
gcloud auth activate-service-account vertex-agent@agi-baby-cherry.iam.gserviceaccount.com --key-file=$GCP_PROJECT_MANAGEMENT_KEY

# Step 3: Set GOOGLE_APPLICATION_CREDENTIALS environment variable
echo "Setting GOOGLE_APPLICATION_CREDENTIALS environment variable..."
export GOOGLE_APPLICATION_CREDENTIALS=$GCP_PROJECT_MANAGEMENT_KEY
echo "export GOOGLE_APPLICATION_CREDENTIALS=$GCP_PROJECT_MANAGEMENT_KEY" >> ~/.bashrc
source ~/.bashrc

# Step 4: Initialize Vertex AI SDK
echo "Initializing Vertex AI SDK with project agi-baby-cherry..."
# This step assumes Python and necessary libraries are installed
python3 -c "from google.cloud import aiplatform; aiplatform.init(project='agi-baby-cherry', location='us-central1'); print('Vertex AI SDK initialized successfully')"

echo "Authentication setup completed. Vertex AI and Gemini calls will now use the service account vertex-agent@agi-baby-cherry.iam.gserviceaccount.com for authentication."
echo "Please ensure the path to the service account key file is correctly set in the script before running."