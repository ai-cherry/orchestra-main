# Quick GCP Authentication and Deployment Guide

This guide provides direct, actionable steps to authenticate with GCP and deploy an application immediately.

## Step 1: Authenticate with GCP (One-Command Setup)

```bash
# Save service account key to file
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

# Authenticate with gcloud
gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=service-account-key.json

# Set project
gcloud config set project cherry-ai-project
```

## Step 2: Quick Deployment Options

### Option A: Deploy to Cloud Run (Containerized Applications)

```bash
# Create a simple Dockerfile if you don't have one
cat > Dockerfile << 'EOL'
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOL

# Create a simple index.html
echo "<html><body><h1>Deployed to GCP!</h1></body></html>" > index.html

# Build and push the container
gcloud builds submit --tag gcr.io/cherry-ai-project/quick-deploy

# Deploy to Cloud Run
gcloud run deploy quick-deploy \
  --image gcr.io/cherry-ai-project/quick-deploy \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option B: Deploy to App Engine (Serverless Applications)

```bash
# Create app.yaml
cat > app.yaml << 'EOL'
runtime: python39
handlers:
- url: /.*
  script: auto
EOL

# Create main.py
cat > main.py << 'EOL'
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Successfully deployed to GCP App Engine!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOL

# Create requirements.txt
echo "flask==2.0.1" > requirements.txt

# Deploy to App Engine
gcloud app deploy --quiet
```

### Option C: Deploy a Cloud Function

```bash
# Create function file
mkdir -p function-deploy
cd function-deploy

# Create main.py for the function
cat > main.py << 'EOL'
def hello_world(request):
    return 'Successfully deployed to GCP Cloud Functions!'
EOL

# Create requirements.txt
echo "flask==2.0.1" > requirements.txt

# Deploy the function
gcloud functions deploy hello-function \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated
```

## Step 3: Verify Deployment

### For Cloud Run:
```bash
# Get the deployed URL
CLOUD_RUN_URL=$(gcloud run services describe quick-deploy --platform managed --region us-central1 --format='value(status.url)')
echo "Your application is deployed at: $CLOUD_RUN_URL"

# Test the deployment
curl $CLOUD_RUN_URL
```

### For App Engine:
```bash
# Get the deployed URL
APP_ENGINE_URL=$(gcloud app describe --format='value(defaultHostname)')
echo "Your application is deployed at: https://$APP_ENGINE_URL"

# Test the deployment
curl https://$APP_ENGINE_URL
```

### For Cloud Function:
```bash
# Get the deployed URL
FUNCTION_URL=$(gcloud functions describe hello-function --format='value(httpsTrigger.url)')
echo "Your function is deployed at: $FUNCTION_URL"

# Test the deployment
curl $FUNCTION_URL
```

## Step 4: Set Up Continuous Deployment (Optional)

```bash
# Create a Cloud Build trigger for GitHub
gcloud builds triggers create github \
  --repo-name=YOUR_GITHUB_REPO \
  --branch-pattern=main \
  --build-config=cloudbuild.yaml

# Create a simple cloudbuild.yaml
cat > cloudbuild.yaml << 'EOL'
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/quick-deploy', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/quick-deploy']
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args: ['run', 'deploy', 'quick-deploy', '--image', 'gcr.io/$PROJECT_ID/quick-deploy', '--platform', 'managed', '--region', 'us-central1', '--allow-unauthenticated']
EOL
```

## Troubleshooting

If you encounter any issues:

1. Check service account permissions:
```bash
gcloud projects get-iam-policy cherry-ai-project --format=json
```

2. Ensure APIs are enabled:
```bash
# Enable necessary APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com appengine.googleapis.com cloudfunctions.googleapis.com
```

3. Check deployment logs:
```bash
# For Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=quick-deploy" --limit=10

# For App Engine
gcloud app logs read --limit=10

# For Cloud Functions
gcloud functions logs read hello-function --limit=10
