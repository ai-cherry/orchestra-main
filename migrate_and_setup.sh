#!/bin/bash
# real_migration_steps.sh

# -----[ Configuration ]-----
export GCP_PROJECT_ID="cherry-ai-project"
export GCP_ORG_ID="873291114285"  # Combined numeric ID from your info
export SERVICE_ACCOUNT_KEY="$(echo $VERTEX_AGENT_KEY | base64 -d)"
export ADMIN_EMAIL="scoobyjava@cherry-ai.me"
export WORKSTATION_PASSWORD="Huskers15"

# -----[ Prerequisite Checks ]-----
check_prerequisites() {
  command -v gcloud >/dev/null 2>&1 || { echo >&2 "gcloud not found. Installing..."; 
    curl https://sdk.cloud.google.com | bash; exec -l $SHELL; }
  command -v terraform >/dev/null 2>&1 || { echo >&2 "terraform not found. Installing...";
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -;
    sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main";
    sudo apt update && sudo apt install terraform; }
}

# -----[ Authentication ]-----
authenticate_gcp() {
  echo "${SERVICE_ACCOUNT_KEY}" > service-account.json
  gcloud auth activate-service-account vertex-agent@cherry-ai-project.iam.gserviceaccount.com \
    --key-file=service-account.json
  gcloud config set project $GCP_PROJECT_ID
}

# -----[ Project Migration ]-----
migrate_project() {
  echo "Migrating project to organization..."
  gcloud beta projects move $GCP_PROJECT_ID --organization=$GCP_ORG_ID
  
  # Verify migration
  CURRENT_ORG=$(gcloud projects describe $GCP_PROJECT_ID --format="value(parent.id)")
  [ "$CURRENT_ORG" == "$GCP_ORG_ID" ] || { echo "Migration failed!"; exit 1; }
}

# -----[ Infrastructure Setup ]-----
setup_infrastructure() {
  # Enable required APIs
  gcloud services enable \
    workstations.googleapis.com \
    redis.googleapis.com \
    alloydb.googleapis.com \
    aiplatform.googleapis.com

  # Create Redis instance
  gcloud redis instances create agent-memory \
    --region=us-west4 \
    --zone=us-west4-a \
    --tier=basic \
    --size=5 \
    --redis-version=redis_6_x

  # Create AlloyDB cluster
  gcloud alloydb clusters create agent-storage \
    --region=us-west4 \
    --password=$WORKSTATION_PASSWORD \
    --network=default
}

# -----[ Hybrid IDE Deployment ]-----
deploy_workstations() {
  cat > hybrid_workstation_config.tf <<EOF
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "4.83.0"
    }
  }
}

resource "google_workstations_workstation_cluster" "ai_cluster" {
  provider               = google-beta
  project                = "$GCP_PROJECT_ID"
  workstation_cluster_id = "ai-development"
  network                = "projects/$GCP_PROJECT_ID/global/networks/default"
  subnetwork             = "projects/$GCP_PROJECT_ID/regions/us-west4/subnetworks/default"
  location               = "us-west4"
}

resource "google_workstations_workstation_config" "ai_config" {
  provider               = google-beta
  workstation_config_id  = "ai-dev-config"
  workstation_cluster_id = google_workstations_workstation_cluster.ai_cluster.workstation_cluster_id
  location               = "us-west4"

  host {
    gce_instance {
      machine_type     = "n2d-standard-32"
      accelerator {
        type  = "nvidia-tesla-t4"
        count = 2
      }
      boot_disk_size_gb = 500
    }
  }

  persistent_directories {
    mount_path = "/home/ai"
    gce_pd {
      size_gb        = 1000
      fs_type        = "ext4"
      disk_type      = "pd-ssd"
      reclaim_policy = "RETAIN"
    }
  }
}
EOF

  terraform init
  terraform apply -auto-approve
}

# -----[ Main Execution ]-----
main() {
  check_prerequisites
  authenticate_gcp
  migrate_project
  setup_infrastructure
  deploy_workstations
  echo "Migration and setup complete! Use 'gcloud workstations start' to access your environment."
}

main
