# Service Accounts for AI Orchestra Project
# This file defines service accounts and IAM roles for Vertex AI and Gemini services

# Vertex AI Administrator Service Account
resource "google_service_account" "vertex_ai_admin" {
  account_id   = "vertex-ai-admin"
  display_name = "Vertex AI Administrator"
  description  = "Service account for Vertex AI operations"
  project      = var.project_id
}

# IAM role bindings for Vertex AI Admin
resource "google_project_iam_binding" "vertex_ai_admin_bindings" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  
  members = [
    "serviceAccount:${google_service_account.vertex_ai_admin.email}",
  ]
}

resource "google_project_iam_binding" "vertex_ai_user_bindings" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  
  members = [
    "serviceAccount:${google_service_account.vertex_ai_admin.email}",
  ]
}

resource "google_project_iam_binding" "vertex_ai_storage_bindings" {
  project = var.project_id
  role    = "roles/storage.admin"
  
  members = [
    "serviceAccount:${google_service_account.vertex_ai_admin.email}",
  ]
}

# Gemini API Administrator Service Account
resource "google_service_account" "gemini_api_admin" {
  account_id   = "gemini-api-admin"
  display_name = "Gemini API Administrator"
  description  = "Service account for Gemini API operations"
  project      = var.project_id
}

# IAM role bindings for Gemini API Admin
resource "google_project_iam_binding" "gemini_api_admin_bindings" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  
  members = [
    "serviceAccount:${google_service_account.gemini_api_admin.email}",
  ]
}

resource "google_project_iam_binding" "gemini_api_user_bindings" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  
  members = [
    "serviceAccount:${google_service_account.gemini_api_admin.email}",
  ]
}

# Secret Management Administrator Service Account
resource "google_service_account" "secret_management_admin" {
  account_id   = "secret-management-admin"
  display_name = "Secret Management Administrator"
  description  = "Service account for Secret Manager operations"
  project      = var.project_id
}

# IAM role bindings for Secret Management Admin
resource "google_project_iam_binding" "secret_mgmt_admin_bindings" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  
  members = [
    "serviceAccount:${google_service_account.secret_management_admin.email}",
  ]
}

resource "google_project_iam_binding" "secret_mgmt_accessor_bindings" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.secret_management_admin.email}",
  ]
}

# Outputs for service account emails
output "vertex_ai_admin_email" {
  description = "Email address of the Vertex AI Admin service account"
  value       = google_service_account.vertex_ai_admin.email
}

output "gemini_api_admin_email" {
  description = "Email address of the Gemini API Admin service account"
  value       = google_service_account.gemini_api_admin.email
}

output "secret_management_admin_email" {
  description = "Email address of the Secret Management Admin service account"
  value       = google_service_account.secret_management_admin.email
}