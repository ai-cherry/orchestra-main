# Performance-optimized Cloud Run configuration for AI Orchestra
# This configuration prioritizes stability and performance over cost
# With improved security, parameterization, and resource management

# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com"
  ])

  service            = each.key
  disable_on_destroy = false
}

# Create Artifact Registry repository for container images
resource "google_artifact_registry_repository" "ai_orchestra_repo" {
  provider      = google
  location      = var.region
  repository_id = "ai-orchestra-${var.env}"
  description   = "Docker repository for AI Orchestra ${var.env} environment"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}