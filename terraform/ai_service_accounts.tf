# AI Service Accounts Configuration
# This file configures the AI service accounts for Vertex AI and Gemini

module "ai_service_accounts" {
  source = "./modules/ai-service-accounts"

  project_id       = var.project_id
  region           = var.region
  env              = var.env
  github_actions_sa = "github-actions@${var.project_id}.iam.gserviceaccount.com"
}

# Output the service account emails for reference
output "vertex_power_user_email" {
  description = "Email address of the Vertex AI Power User service account"
  value       = module.ai_service_accounts.vertex_power_user_email
}

output "gemini_power_user_email" {
  description = "Email address of the Gemini Power User service account"
  value       = module.ai_service_accounts.gemini_power_user_email
}

# Create a Cloud Run service account binding to allow access to Vertex AI
resource "google_project_iam_member" "cloud_run_vertex_access" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"

  depends_on = [module.ai_service_accounts]
}

# Create a Cloud Run service account binding to allow access to Secret Manager
resource "google_project_iam_member" "cloud_run_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"

  depends_on = [module.ai_service_accounts]
}

# Allow Cloud Run service to access the Vertex AI service account key
resource "google_secret_manager_secret_iam_member" "cloud_run_vertex_key_access" {
  project   = var.project_id
  secret_id = module.ai_service_accounts.vertex_power_key_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_service_account.email}"

  depends_on = [module.ai_service_accounts]
}

# Allow Cloud Run service to access the Gemini service account key
resource "google_secret_manager_secret_iam_member" "cloud_run_gemini_key_access" {
  project   = var.project_id
  secret_id = module.ai_service_accounts.gemini_power_key_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_service_account.email}"

  depends_on = [module.ai_service_accounts]
}