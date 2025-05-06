# AI Service Accounts Terraform Module
# This module creates and manages service accounts for Vertex AI and Gemini

# Vertex AI Administrator Service Account
resource "google_service_account" "vertex_power_user" {
  account_id   = "vertex-power-user"
  display_name = "Vertex AI Power User"
  description  = "Service account with extensive permissions for Vertex AI operations"
  project      = var.project_id
}

# IAM role bindings for Vertex AI Power User
resource "google_project_iam_member" "vertex_power_user_bindings" {
  for_each = toset([
    "roles/aiplatform.admin",
    "roles/aiplatform.user",
    "roles/storage.admin",
    "roles/logging.admin",
    "roles/monitoring.admin",
    "roles/secretmanager.secretAccessor",
    "roles/iam.serviceAccountUser",
    "roles/iam.serviceAccountTokenCreator",
    "roles/compute.admin",
    "roles/serviceusage.serviceUsageAdmin"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.vertex_power_user.email}"
}

# Gemini API Administrator Service Account
resource "google_service_account" "gemini_power_user" {
  account_id   = "gemini-power-user"
  display_name = "Gemini Power User"
  description  = "Service account with extensive permissions for Gemini operations"
  project      = var.project_id
}

# IAM role bindings for Gemini Power User
resource "google_project_iam_member" "gemini_power_user_bindings" {
  for_each = toset([
    "roles/aiplatform.admin",
    "roles/aiplatform.user",
    "roles/storage.admin",
    "roles/logging.admin",
    "roles/monitoring.admin",
    "roles/secretmanager.secretAccessor",
    "roles/iam.serviceAccountUser",
    "roles/iam.serviceAccountTokenCreator",
    "roles/serviceusage.serviceUsageAdmin"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.gemini_power_user.email}"
}

# Secret Manager secret for Vertex AI service account key
resource "google_secret_manager_secret" "vertex_power_key" {
  secret_id = "vertex-power-key"
  project   = var.project_id
  
  replication {
    auto {}
  }
}

# Secret Manager secret for Gemini service account key
resource "google_secret_manager_secret" "gemini_power_key" {
  secret_id = "gemini-power-key"
  project   = var.project_id
  
  replication {
    auto {}
  }
}

# IAM binding to allow GitHub Actions to access the secrets
resource "google_secret_manager_secret_iam_member" "vertex_power_key_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.vertex_power_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.github_actions_sa}"
}

resource "google_secret_manager_secret_iam_member" "gemini_power_key_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.gemini_power_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.github_actions_sa}"
}