locals {
  project_id = "cherry-ai.me"
  project_number = "525398941159"
  registry_path = "us-central1-docker.pkg.dev/${local.project_id}/orchestra"
  service_account_email = "vertex-agent@${local.project_id}.iam.gserviceaccount.com"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "compute.googleapis.com"
  ])

  project = local.project_id
  service = each.key
  disable_dependent_services = false
  disable_on_destroy = false
}

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "orchestra" {
  provider = google-beta
  project = local.project_id
  location = var.region
  repository_id = var.registry_name
  description = "Docker repository for Orchestra services"
  format = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# Create Cloud Storage buckets
resource "google_storage_bucket" "artifacts" {
  name = "${var.storage_bucket_prefix}-artifacts"
  location = var.region
  project = local.project_id
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "models" {
  name = "${var.storage_bucket_prefix}-model-artifacts"
  location = var.region
  project = local.project_id
  uniform_bucket_level_access = true
}

# Deploy Cloud Run service
resource "google_cloud_run_service" "orchestra_api" {
  name = "orchestra-${var.environment}"
  location = var.region
  project = local.project_id

  template {
    spec {
      containers {
        image = "${local.registry_path}/api:latest"
        env {
          name = "PROJECT_ID"
          value = local.project_id
        }
        env {
          name = "ENVIRONMENT"
          value = var.environment
        }
      }
      service_account_name = local.service_account_email
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }

  depends_on = [google_project_service.required_apis]
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  count = var.environment == "dev" ? 1 : 0
  location = google_cloud_run_service.orchestra_api.location
  project = google_cloud_run_service.orchestra_api.project
  service = google_cloud_run_service.orchestra_api.name
  role = "roles/run.invoker"
  member = "allUsers"
}

# Create secrets in Secret Manager
resource "google_secret_manager_secret" "secrets" {
  for_each = toset([
    "OPENAI_API_KEY",
    "PORTKEY_API_KEY",
    "OPENROUTER_API_KEY"
  ])

  secret_id = each.key
  project = local.project_id

  replication {
    automatic = true
  }

  depends_on = [google_project_service.required_apis]
}