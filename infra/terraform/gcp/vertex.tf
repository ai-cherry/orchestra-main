locals {
  vertex_service_account = "vertex-agent@cherry-ai.me.iam.gserviceaccount.com"
  model_registry = "us-central1-docker.pkg.dev/cherry-ai.me/ai-models"
}

# Create AI Platform model registry
resource "google_artifact_registry_repository" "ai_models" {
  provider = google-beta
  project = "cherry-ai.me"
  location = var.region
  repository_id = "ai-models"
  description = "Docker repository for AI models"
  format = "DOCKER"
}

# Create model storage bucket
resource "google_storage_bucket" "model_artifacts" {
  name = "cherry-ai-me-model-artifacts"
  location = var.region
  project = "cherry-ai.me"
  uniform_bucket_level_access = true
}

# Create Vertex AI endpoint
resource "google_vertex_ai_endpoint" "model_endpoint" {
  provider = google-beta
  project = "cherry-ai.me"
  display_name = "orchestra-model-endpoint"
  location = var.region
  network = "projects/525398941159/global/networks/default"

  depends_on = [google_project_service.required_apis]
}

# Grant necessary IAM roles to the Vertex AI service account
resource "google_project_iam_member" "vertex_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/artifactregistry.reader"
  ])

  project = "cherry-ai.me"
  role = each.key
  member = "serviceAccount:${local.vertex_service_account}"
}