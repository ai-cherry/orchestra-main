/**
 * Orchestra Infrastructure Configuration - Production Environment
 *
 * This configuration creates the production environment for the Orchestra platform,
 * including Cloud Run services, Firestore database, Pub/Sub topics, and Vector Search.
 */

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

  # Uncomment to use a GCS backend for state
  # backend "gcs" {
  #   bucket = "agi-baby-cherry-terraform-state"
  #   prefix = "orchestra/prod"
  # }
}

provider "google" {
  project     = var.project_id
  region      = var.region
  zone        = "${var.region}-a"
  credentials = file(var.credentials_file)
}

provider "google-beta" {
  project     = var.project_id
  region      = var.region
  zone        = "${var.region}-a"
  credentials = file(var.credentials_file)
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "agi-baby-cherry"
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-west2"
}

variable "env" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "credentials_file" {
  description = "Path to the GCP credentials file"
  type        = string
  default     = "/tmp/gsa-key.json"
}

# Cloud Run Service
module "cloud_run" {
  source = "../modules/cloud-run"

  project_id          = var.project_id
  region              = var.region
  env                 = var.env
  image               = "us-west2-docker.pkg.dev/${var.project_id}/orchestra/orchestrator:${var.env}-latest"
  min_instances       = 1  # Keep at least one instance running in production
  max_instances       = 50 # Higher cap for production
  cpu_always_allocated = true
  firestore_namespace = "orchestra-${var.env}"
  vector_index_name   = "orchestra-embeddings-${var.env}"
}

# Firestore Database
module "firestore" {
  source = "../modules/firestore"

  project_id = var.project_id
  region     = var.region
  env        = var.env
}

# Pub/Sub Topics
module "pubsub" {
  source = "../modules/pubsub"

  project_id = var.project_id
  env        = var.env
}

# Vertex AI Vector Search
module "vertex" {
  source = "../modules/vertex"

  project_id       = var.project_id
  region           = var.region
  env              = var.env
  index_replicas   = 2  # Higher replica count for production
  vector_dimension = 1536  # Assuming OpenAI embedding dimension
}

# Secret Manager for API Keys
resource "google_secret_manager_secret" "openrouter" {
  secret_id = "openrouter-${var.env}"
  
  replication {
    automatic = true
  }
}

# Grant access to the Cloud Run service account
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.openrouter.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.cloud_run.service_account}"
}

# Outputs
output "cloud_run_url" {
  value = module.cloud_run.url
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
