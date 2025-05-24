#!/bin/bash
# GCP Bootstrap Script: Automated setup for high-performance AI/data orchestration
# Integrates Cloud Run, DragonflyDB (on GKE), Firestore, Pub/Sub, Secret Manager, and VPC peering.
# Designed for single-developer, performance-first workflows.

set -e

# ---- CONFIGURATION ----
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${REGION:-us-central1}"
DRAGONFLY_GKE_CLUSTER="dragonfly-cluster"
DRAGONFLY_NAMESPACE="dragonfly"
DRAGONFLY_RELEASE="dragonfly"
DRAGONFLY_IMAGE="docker.io/dragonflydb/dragonfly:latest"
CLOUD_RUN_SERVICE="orchestra-api"
PUBSUB_TOPIC="orchestra-events"
SECRETS=("gong_access_key" "gong_access_key_secret" "elevenlabs_api_key" "slack_client_id" "slack_client_secret" "slack_signing_secret" "slack_app_token" "slackbot_token" "slack_refresh_token" "slack_socket_token" "salesforce_access_token" "venice_ai_api_key" "estuary_api_key")

echo "Using GCP Project: $PROJECT_ID"
echo "Region: $REGION"

# ---- ENABLE REQUIRED APIS ----
echo "Enabling required GCP APIs..."
gcloud services enable run.googleapis.com \
    container.googleapis.com \
    firestore.googleapis.com \
    pubsub.googleapis.com \
    secretmanager.googleapis.com \
    vpcaccess.googleapis.com

# ---- FIRESTORE SETUP ----
echo "Setting up Firestore (Native mode)..."
gcloud firestore databases create --region="$REGION" --project="$PROJECT_ID" || true

# ---- PUB/SUB SETUP ----
echo "Creating Pub/Sub topic..."
gcloud pubsub topics create "$PUBSUB_TOPIC" --project="$PROJECT_ID" || true

# ---- SECRET MANAGER SETUP ----
echo "Creating secrets in Secret Manager..."
for SECRET in "${SECRETS[@]}"; do
  if ! gcloud secrets describe "$SECRET" --project="$PROJECT_ID" >/dev/null 2>&1; then
    gcloud secrets create "$SECRET" --replication-policy="automatic" --project="$PROJECT_ID"
    echo "Created secret: $SECRET"
  else
    echo "Secret $SECRET already exists."
  fi
done

# ---- GKE CLUSTER FOR DRAGONFLYDB ----
echo "Provisioning GKE cluster for DragonflyDB..."
gcloud container clusters create "$DRAGONFLY_GKE_CLUSTER" \
    --region "$REGION" \
    --num-nodes "1" \
    --machine-type "e2-standard-2" \
    --enable-autoscaling --min-nodes "1" --max-nodes "3" \
    --project "$PROJECT_ID" || true

gcloud container clusters get-credentials "$DRAGONFLY_GKE_CLUSTER" --region "$REGION" --project "$PROJECT_ID"

kubectl create namespace "$DRAGONFLY_NAMESPACE" || true

echo "Deploying DragonflyDB to GKE..."
kubectl -n "$DRAGONFLY_NAMESPACE" run "$DRAGONFLY_RELEASE" \
    --image="$DRAGONFLY_IMAGE" \
    --port=6379 \
    --restart=Always \
    --requests='cpu=500m,memory=1Gi' \
    --expose || true

# Expose DragonflyDB via LoadBalancer (for GCP-internal use)
kubectl -n "$DRAGONFLY_NAMESPACE" expose pod "$DRAGONFLY_RELEASE" \
    --type=LoadBalancer \
    --port=6379 \
    --target-port=6379 || true

# ---- CLOUD RUN SETUP ----
echo "Deploying Cloud Run service (placeholder image)..."
gcloud run deploy "$CLOUD_RUN_SERVICE" \
    --image="gcr.io/cloudrun/hello" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --cpu=2 \
    --memory=2Gi \
    --concurrency=80 \
    --set-env-vars="DRAGONFLY_URL=redis://$(kubectl -n $DRAGONFLY_NAMESPACE get svc $DRAGONFLY_RELEASE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):6379" \
    --project="$PROJECT_ID"

# ---- VPC CONNECTOR (OPTIONAL) ----
echo "Setting up VPC Access Connector for private networking..."
gcloud compute networks vpc-access connectors create orchestra-vpc-connector \
    --region "$REGION" \
    --range "10.8.0.0/28" \
    --project "$PROJECT_ID" || true

# ---- SUMMARY ----
echo "GCP environment bootstrap complete."
echo "DragonflyDB running on GKE in namespace '$DRAGONFLY_NAMESPACE'."
echo "Cloud Run service '$CLOUD_RUN_SERVICE' deployed."
echo "Firestore, Pub/Sub, and Secret Manager configured."
echo "You may now deploy your application containers and update Cloud Run with your production image."