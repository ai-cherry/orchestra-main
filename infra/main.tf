terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket  = "agi-baby-cherry-terraform-state"
    prefix  = "orchestra"
  }
}

provider "google" {
  project     = "agi-baby-cherry"
  region      = var.region
  zone        = "${var.region}-a"
  credentials = file("/tmp/gsa-key.json")
}

provider "google-beta" {
  project     = "agi-baby-cherry"
  region      = var.region
  zone        = "${var.region}-a"
  credentials = file("/tmp/gsa-key.json")
}

# ------------ Variables --------------
variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "Environment must be one of: dev, stage, prod"
  }
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-west2"
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "agi-baby-cherry"
}

# ------------ Storage Bucket for Terraform State --------------
resource "google_storage_bucket" "terraform_state" {
  name          = "agi-baby-cherry-terraform-state"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30  # days
    }
    action {
      type = "Delete"
    }
  }
}

# ------------ Cloud Run --------------
module "orchestrator_run" {
  source = "./modules/cloud-run"

  project_id         = var.project_id
  region             = var.region
  env                = var.env
  image              = "us-west2-docker.pkg.dev/${var.project_id}/orchestra/orchestrator:latest"
  min_instances      = 0
  max_instances      = 20
  cpu_always_allocated = true
  firestore_namespace = "orchestra-${var.env}"
  vector_index_name  = "orchestra-embeddings-${var.env}"
}

# ------------ Firestore --------------
module "firestore" {
  source = "./modules/firestore"

  project_id = var.project_id
  region     = var.region
  env        = var.env
}

# ------------ Pub/Sub ----------------
module "pubsub" {
  source = "./modules/pubsub"

  project_id = var.project_id
  env        = var.env
}

# ------------ Secret Manager ----------
resource "google_secret_manager_secret" "openrouter" {
  secret_id = "openrouter"
  
  replication {
    automatic = true
  }
}

# Grant access to the Cloud Run service account
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.openrouter.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.orchestrator_run.service_account}"
}

# ------------ Vertex Vector Search ----
module "vertex" {
  source = "./modules/vertex"

  project_id      = var.project_id
  region          = var.region
  env             = var.env
  index_replicas  = 1
  vector_dimension = 1536  # Assuming OpenAI embedding dimension
}

# ------------ Artifact Repository ----------
resource "google_artifact_registry_repository" "orchestra" {
  provider = google-beta
  
  location      = var.region
  repository_id = "orchestra"
  description   = "Docker repository for Orchestra services"
  format        = "DOCKER"
}

# ------------ IAM Setup ----------
resource "google_project_iam_member" "vertex_agent_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "vertex_agent_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
}

# ------------ Outputs --------------
output "cloud_run_url" {
  value = module.orchestrator_run.url
  description = "URL of the Cloud Run service"
}

output "firestore_database" {
  value = module.firestore.database_id
  description = "Firestore Database ID"
}

output "pubsub_topic" {
  value = module.pubsub.topic_id
  description = "Pub/Sub Topic ID"
}

output "vector_index" {
  value = module.vertex.index_id
  description = "Vertex AI Vector Search Index ID"
}
