#!/bin/bash
# Script to install Google Cloud SDK without sudo, authenticate, and deploy
# For user: scoobyjava@cherry-ai.me

set -e  # Exit on any error

echo "Starting GCP SDK installation, authentication, and deployment process..."

# Step 1: Install Google Cloud SDK using the generic method (no sudo required)
echo "Installing Google Cloud SDK..."
echo "Using generic installation method (no sudo required)"
curl https://sdk.cloud.google.com > install.sh
bash install.sh --disable-prompts
export PATH=$HOME/google-cloud-sdk/bin:$PATH

# Verify installation
echo "Verifying Google Cloud SDK installation..."
if command -v $HOME/google-cloud-sdk/bin/gcloud &> /dev/null; then
    echo "Google Cloud SDK installed successfully."
    $HOME/google-cloud-sdk/bin/gcloud --version
    # Create an alias for convenience
    alias gcloud=$HOME/google-cloud-sdk/bin/gcloud
else
    echo "Failed to install Google Cloud SDK. Please install it manually."
    exit 1
fi

# Step 2: Create service account key file
echo "Creating service account key file..."
cat > service-account-key.json << 'EOL'
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "216e545f19f380c72ad7eb704a15041621503f03",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDi3y+r4sY+2Jyj\ngdG/N5OrTNMKdhY2nndtxk4V4NVkRdSXKSGE3WEz6bLBaT0iVBXjDhuGyT1IzjiS\nCmkWjQ6CaGCwThjvHjkioHTIsgNO6/7FjCh0YRXJIz+gkY9O2P2UMKDMetlDz6la\nVdaFWHCro/ipoC9dZtiWxX7JoDw6+ZqoYct20qtrRDlh2trF+RT9QzxLJmeWoZxB\nvHU1oU1PsbGPDHyts/iXHqISyjEsUUtvOG/IsvMIWPVWvRCbnweQkktsATqzD7bH\nXZOj4cSqO2imAEPFkK/TZ+56JdjtHoZEaVyxzmXB4Pr9sde6KfuesdXjykufztMR\nwULU1B0fAgMBAAECggEASUsqVwD94+rN/ALiNMDrO5Gnsn8A4Sdj1PqWWnoW5nyq\n2CTpF8f/caqD3fk2T2NT6NUzbmGQI3fADepAFhF/CQFYj0zDwGiGs9mbsQTVjccv\nOTn1DdgZljAFi8XKwwHWNmxZXoYnr8EkaLNHiS/PwpvIJ2DBPI8P1PG76r6SBsjl\n7++ShV9r+m577erGvXUxk80dgYoHfBemwYBLSSm5LW0frSmEKHI7vBIT231YslTy\nYFODMOQQ0t+1MtX+7uNVyYOx+GdERkp9XfB3sgYVxZwdZ2pXha0pOZ2UieAm0Za6\nTNoUvhSYECXBfkMyXz89OaWI+4ycizvW9JziZeLk+QKBgQD5Znm9iYmdmvUYmI6T\nK7nBHDk3IXsJ+rwLOEDLHp0c1dhdgimgzFN81mKibDQ4jefRvTlDqSWbZ7Hn4YMF\nCTyZXgJKlU7A0qlufGWd3gfLGkwlDlzyi209mw7yE4W70sQpasea2e3cVWWYtxy9\nwSYQmxObgVZU5L7feVt1xmOIaQKBgQDo4BhN/6PzdnpyQfow4WLxFRCnjRnAZ4Ka\nLqHt8KB4L9K/3qjLFhJLNAUPcOL0C9K581CFfXqqN4gauKzGYa8id2RB9d8Q7LSE\nLNblKOMA3OoSGlWXDaWXLGLA9IsHyIgUqK6oRkoaW4a8XFN5ntgbJoEDpydfCXTs\nKOnAbIYIRwKBgQCB7U7y3RoiTz3siF2OcjMdVXTBMeIFeuhH+BBZQSOciBNl8494\nQ7oiyRUthK1X4SWp8KhKhW4gHc9i++rjzsIRLBaJgGs8rQKzmn7d1XO97X9JtsfZ\nW6WXeJY6qsz64nxrD0PZejselCaPfqWsfVk1QXTfiGvPYjPF/FUXcDkeMQKBgEOY\nYJWrYZyWxF4L9qJfmceetLHdzB7ELO2yIYCeewXH4+WbrOUeJ/s6Q0nDG615DRa6\noKHO1V85NUGEX2pKCnr3qttWkgQooRFIrqvf3Vxvw2WzzSpGZM1nrdaSZRTCSXWt\nrNzdYj8aWBauufAwgkwHNiWoTE5SwWSXT5pyJcmbAoGBALODSSlDnCtXqMry+lKx\nywyhRlYIk2QsmUjrJdYd74o6C8Q7D6o/p1Ah3uNl5fKvN+0QeNvpJB9yqiauS+w2\nlEMmVdcqYKwdmjkPxGiLKHhJcXiB62Nd5jUtVvGv9lz1c74bJdmhYjUOGuUtR5Ll\nxFFGN62B4+ed1wDppnemICJV\n-----END PRIVATE KEY-----\n",
  "client_email": "orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "103717197419391442785",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/orchestra-project-admin-sa%40cherry-ai-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOL

# Secure the file
chmod 600 service-account-key.json
echo "Service account key file created and secured."

# Step 3: Authenticate with gcloud
echo "Authenticating with GCP..."
$HOME/google-cloud-sdk/bin/gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=service-account-key.json
$HOME/google-cloud-sdk/bin/gcloud config set project cherry-ai-project
echo "Authentication successful."

# Step 4: Enable necessary APIs
echo "Enabling necessary GCP APIs..."
$HOME/google-cloud-sdk/bin/gcloud services enable cloudbuild.googleapis.com run.googleapis.com storage-api.googleapis.com

# Step 5: Deploy to Cloud Run
echo "Deploying to Cloud Run..."

# Create a simple Dockerfile
cat > Dockerfile << 'EOL'
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOL

# Create a simple index.html
echo "<html><body><h1>Deployed to GCP Cloud Run!</h1><p>Deployment time: $(date)</p><p>Deployed by: scoobyjava@cherry-ai.me</p></body></html>" > index.html

# Build and push the container
echo "Building and pushing container..."
$HOME/google-cloud-sdk/bin/gcloud builds submit --tag gcr.io/cherry-ai-project/quick-deploy

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
$HOME/google-cloud-sdk/bin/gcloud run deploy quick-deploy \
  --image gcr.io/cherry-ai-project/quick-deploy \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Get the deployed URL
CLOUD_RUN_URL=$($HOME/google-cloud-sdk/bin/gcloud run services describe quick-deploy --platform managed --region us-central1 --format='value(status.url)')
echo "Your application is deployed at: $CLOUD_RUN_URL"

echo "Deployment completed successfully!"
echo "You can now access your deployed application at: $CLOUD_RUN_URL"
