#!/bin/bash
# gcp_env_optimize.sh
# Comprehensive GCP environment optimization script for Orchestra AI
# Enables APIs, configures IAM, VPC, Cloud Run, Secret Manager, Redis, AlloyDB, monitoring, and sets quotas.

set -euo pipefail

# --- CONFIGURATION ---
PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
REGION="${GCP_REGION:-us-central1}"
REDIS_INSTANCE="orchestra-redis"
ALLOYDB_INSTANCE="orchestra-alloydb"
NETWORK="orchestra-vpc"
SUBNET="orchestra-subnet"
SERVICE_ACCOUNT="orchestra-sa"
CLOUD_RUN_SERVICE="orchestra-api"

# --- ENABLE CORE APIS ---
echo "Enabling core GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  vpcaccess.googleapis.com \
  iam.googleapis.com \
  secretmanager.googleapis.com \
  redis.googleapis.com \
  alloydb.googleapis.com \
  sqladmin.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  --project="$PROJECT_ID"

# --- CREATE VPC AND SUBNET ---
echo "Configuring VPC and subnet..."
gcloud compute networks create "$NETWORK" --subnet-mode=custom --project="$PROJECT_ID" || true
gcloud compute networks subnets create "$SUBNET" \
  --network="$NETWORK" \
  --range=10.10.0.0/16 \
  --region="$REGION" \
  --project="$PROJECT_ID" || true

# --- CREATE SERVICE ACCOUNT ---
echo "Creating service account..."
gcloud iam service-accounts create "$SERVICE_ACCOUNT" \
  --display-name="Orchestra Service Account" \
  --project="$PROJECT_ID" || true

# --- ASSIGN IAM ROLES ---
echo "Assigning IAM roles..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/owner"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/redis.admin"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/alloydb.admin"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# --- CREATE REDIS INSTANCE ---
echo "Provisioning Redis (MemoryStore)..."
gcloud redis instances create "$REDIS_INSTANCE" \
  --size=4 --region="$REGION" --tier=STANDARD_HA \
  --network="projects/$PROJECT_ID/global/networks/$NETWORK" \
  --project="$PROJECT_ID" || true

# --- CREATE ALLOYDB INSTANCE ---
echo "Provisioning AlloyDB..."
gcloud alloydb instances create "$ALLOYDB_INSTANCE" \
  --region="$REGION" \
  --network="projects/$PROJECT_ID/global/networks/$NETWORK" \
  --project="$PROJECT_ID" || true

# --- CREATE SECRET MANAGER ENTRIES ---
echo "Creating Secret Manager entries (example)..."
gcloud secrets create orchestra-api-key --replication-policy="automatic" --project="$PROJECT_ID" || true
echo "your-api-key-value" | gcloud secrets versions add orchestra-api-key --data-file=- --project="$PROJECT_ID"

# --- SET QUOTAS (EXAMPLES) ---
echo "Setting quotas (manual review recommended)..."
# gcloud compute project-info describe --project="$PROJECT_ID"
# gcloud compute regions describe "$REGION" --project="$PROJECT_ID"
# Quota increases must be requested via GCP Console.

# --- ENABLE MONITORING & LOGGING ---
echo "Configuring monitoring and logging..."
gcloud monitoring dashboards create --config-from-file=monitoring/prometheus.yml --project="$PROJECT_ID" || true

# --- DEPLOY CLOUD RUN SERVICE (PLACEHOLDER) ---
echo "Deploying Cloud Run service (placeholder)..."
# gcloud run deploy "$CLOUD_RUN_SERVICE" --image=gcr.io/$PROJECT_ID/orchestra-api:latest --region="$REGION" --platform=managed --allow-unauthenticated --project="$PROJECT_ID"

echo "GCP environment optimization complete. Review output and logs for any manual actions required."
