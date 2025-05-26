#!/bin/bash
# AI Orchestra Deployment Script
# ==============================
# Deploys the complete AI Orchestra + SuperAGI stack

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Check prerequisites
log_info "Checking prerequisites..."
check_command gcloud
check_command pulumi
check_command kubectl
check_command python3

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    log_error "No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi
log_info "Using GCP project: $PROJECT_ID"

# Set environment variables
export PULUMI_CONFIG_PASSPHRASE=""  # For automation
ENVIRONMENT=${ENVIRONMENT:-dev}
REGION=${REGION:-us-central1}
ZONE=${ZONE:-${REGION}-a}

log_info "Environment: $ENVIRONMENT"
log_info "Region: $REGION"
log_info "Zone: $ZONE"

# Step 1: Enable required APIs
log_info "Enabling required GCP APIs..."
gcloud services enable \
    container.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    --project=$PROJECT_ID

# Step 2: Create backup bucket
BACKUP_BUCKET="orchestra-backups-${PROJECT_ID}"
if ! gsutil ls -b gs://${BACKUP_BUCKET} &> /dev/null; then
    log_info "Creating backup bucket..."
    gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${BACKUP_BUCKET}

    # Set lifecycle rule
    cat > /tmp/lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF
    gsutil lifecycle set /tmp/lifecycle.json gs://${BACKUP_BUCKET}
    rm /tmp/lifecycle.json
else
    log_info "Backup bucket already exists"
fi

# Step 3: Set up Pulumi
log_info "Setting up Pulumi..."
cd infra

# Initialize Pulumi if needed
if [ ! -d ".pulumi" ]; then
    pulumi login --local
    pulumi stack init ${ENVIRONMENT} || true
fi

# Select stack
pulumi stack select ${ENVIRONMENT}

# Set configuration
log_info "Setting Pulumi configuration..."
pulumi config set gcp_project_id ${PROJECT_ID}
pulumi config set region ${REGION}
pulumi config set zone ${ZONE}

# Check for required secrets
if ! pulumi config get openai_api_key --secret &> /dev/null; then
    log_warn "OpenAI API key not set. Please run:"
    log_warn "pulumi config set --secret openai_api_key YOUR_KEY"
fi

if ! pulumi config get weaviate_api_key --secret &> /dev/null; then
    log_warn "Weaviate API key not set. Please run:"
    log_warn "pulumi config set --secret weaviate_api_key YOUR_KEY"
fi

if ! pulumi config get weaviate_rest_endpoint &> /dev/null; then
    log_info "Setting default Weaviate endpoint..."
    pulumi config set weaviate_rest_endpoint "http://weaviate.superagi.svc.cluster.local:8080"
fi

if ! pulumi config get grafana_admin_password --secret &> /dev/null; then
    log_info "Generating Grafana admin password..."
    GRAFANA_PASSWORD=$(openssl rand -base64 32)
    pulumi config set --secret grafana_admin_password ${GRAFANA_PASSWORD}
    log_info "Grafana admin password set (saved in Pulumi config)"
fi

# Step 4: Deploy infrastructure
log_info "Deploying infrastructure with Pulumi..."
pulumi up --yes

# Step 5: Get outputs
log_info "Getting deployment outputs..."
CLUSTER_NAME=$(pulumi stack output cluster_name)
SUPERAGI_ENDPOINT=$(pulumi stack output superagi_endpoint 2>/dev/null || echo "pending")
GRAFANA_ENDPOINT=$(pulumi stack output grafana_endpoint 2>/dev/null || echo "pending")
PROMETHEUS_ENDPOINT=$(pulumi stack output prometheus_endpoint 2>/dev/null || echo "pending")

# Step 6: Configure kubectl
log_info "Configuring kubectl..."
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID}

# Step 7: Wait for services to be ready
log_info "Waiting for services to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n superagi || true
kubectl wait --for=condition=available --timeout=300s deployment --all -n monitoring || true

# Step 8: Run initial backup
log_info "Running initial backup..."
cd ../scripts
python3 backup_manager.py \
    --project-id ${PROJECT_ID} \
    --backup-bucket ${BACKUP_BUCKET} \
    --run-backup || log_warn "Initial backup failed - this is normal if services are still starting"

# Step 9: Create backup CronJob
log_info "Creating backup CronJob..."
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-cronjob
  namespace: superagi
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: superagi-sa
          containers:
          - name: backup
            image: google/cloud-sdk:alpine
            command:
            - /bin/sh
            - -c
            - |
              pip install redis google-cloud-storage google-cloud-firestore kubernetes
              python /scripts/backup_manager.py --project-id ${PROJECT_ID} --backup-bucket ${BACKUP_BUCKET} --run-backup
            volumeMounts:
            - name: backup-script
              mountPath: /scripts
          volumes:
          - name: backup-script
            configMap:
              name: backup-script
          restartPolicy: OnFailure
EOF

# Create ConfigMap with backup script
kubectl create configmap backup-script --from-file=backup_manager.py -n superagi --dry-run=client -o yaml | kubectl apply -f -

# Step 10: Display summary
log_info "Deployment complete!"
echo ""
echo "==================================="
echo "AI Orchestra Deployment Summary"
echo "==================================="
echo "Project ID: ${PROJECT_ID}"
echo "Environment: ${ENVIRONMENT}"
echo "Cluster: ${CLUSTER_NAME}"
echo ""
echo "Endpoints:"
echo "- SuperAGI: ${SUPERAGI_ENDPOINT}"
echo "- Grafana: ${GRAFANA_ENDPOINT}"
echo "- Prometheus: ${PROMETHEUS_ENDPOINT}"
echo ""
echo "Next steps:"
echo "1. Access Grafana:"
echo "   kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "   Open http://localhost:3000 (admin/[password in Pulumi config])"
echo ""
echo "2. Access SuperAGI:"
echo "   kubectl port-forward -n superagi svc/superagi 8080:8080"
echo "   Open http://localhost:8080"
echo ""
echo "3. Run performance tests:"
echo "   python scripts/performance_test.py --endpoint http://localhost:8080 --test all"
echo ""
echo "4. Check backup status:"
echo "   python scripts/backup_manager.py --project-id ${PROJECT_ID} --backup-bucket ${BACKUP_BUCKET} --verify"
echo "==================================="
