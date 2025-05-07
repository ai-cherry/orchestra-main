# Terraform configuration for setting up "badass" Vertex AI and Gemini service accounts
# Using existing credentials from cherry-ai-project

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "cherry-ai-project"
  region  = "us-central1"
}

provider "google-beta" {
  project = "cherry-ai-project"
  region  = "us-central1"
}

# Create a "badass" Vertex AI service account with extensive permissions
resource "google_service_account" "vertex_ai_badass" {
  account_id   = "vertex-ai-badass"
  display_name = "Vertex AI Badass Service Account"
  description  = "Service account with extensive permissions for all Vertex AI operations"
}

# Grant comprehensive roles to the Vertex AI service account
resource "google_project_iam_member" "vertex_ai_admin" {
  project = "cherry-ai-project"
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

resource "google_project_iam_member" "vertex_ai_user" {
  project = "cherry-ai-project"
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

resource "google_project_iam_member" "vertex_storage_admin" {
  project = "cherry-ai-project"
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

resource "google_project_iam_member" "vertex_logging_admin" {
  project = "cherry-ai-project"
  role    = "roles/logging.admin"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

resource "google_project_iam_member" "vertex_service_account_user" {
  project = "cherry-ai-project"
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

resource "google_project_iam_member" "vertex_service_account_token_creator" {
  project = "cherry-ai-project"
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.vertex_ai_badass.email}"
}

# Create a "badass" Gemini service account with extensive permissions
resource "google_service_account" "gemini_badass" {
  account_id   = "gemini-badass"
  display_name = "Gemini Badass Service Account"
  description  = "Service account with extensive permissions for all Gemini API operations"
}

# Grant comprehensive roles to the Gemini service account
resource "google_project_iam_member" "gemini_ai_platform_user" {
  project = "cherry-ai-project"
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.gemini_badass.email}"
}

resource "google_project_iam_member" "gemini_service_usage" {
  project = "cherry-ai-project"
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:${google_service_account.gemini_badass.email}"
}

resource "google_project_iam_member" "gemini_service_account_user" {
  project = "cherry-ai-project"
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.gemini_badass.email}"
}

resource "google_project_iam_member" "gemini_service_account_token_creator" {
  project = "cherry-ai-project"
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.gemini_badass.email}"
}

# Set up Workload Identity Federation for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  provider                  = google-beta
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  provider                           = google-beta
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow GitHub Actions to impersonate the service accounts
resource "google_service_account_iam_binding" "workload_identity_binding_vertex" {
  service_account_id = google_service_account.vertex_ai_badass.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/ai-cherry/orchestra-main"
  ]
}

resource "google_service_account_iam_binding" "workload_identity_binding_gemini" {
  service_account_id = google_service_account.gemini_badass.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/ai-cherry/orchestra-main"
  ]
}

# Outputs
output "vertex_ai_service_account" {
  value = google_service_account.vertex_ai_badass.email
  description = "Email of the Vertex AI badass service account"
}

output "gemini_service_account" {
  value = google_service_account.gemini_badass.email
  description = "Email of the Gemini badass service account"
}

output "workload_identity_provider" {
  value = "projects/cherry-ai-project/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id}"
  description = "Workload Identity Provider for GitHub Actions"
}