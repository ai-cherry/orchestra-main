# Secret Management for AI Orchestra
# Centralizes all authentication tokens and credentials

# Secret for GCP Master Service Account JSON
resource "google_secret_manager_secret" "gcp_master_service_json" {
  secret_id = "gcp-master-service-json"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.env
    managed-by  = "terraform"
    project     = "ai-orchestra"
  }
}

# Secret for GitHub Classic PAT Token
resource "google_secret_manager_secret" "gh_classic_pat_token" {
  secret_id = "gh-classic-pat-token"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.env
    managed-by  = "terraform"
    project     = "ai-orchestra"
  }
}

# Secret for GitHub Fine-Grained PAT Token
resource "google_secret_manager_secret" "gh_fine_grained_pat_token" {
  secret_id = "gh-fine-grained-pat-token"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.env
    managed-by  = "terraform"
    project     = "ai-orchestra"
  }
}

# IAM bindings for service accounts to access secrets
resource "google_secret_manager_secret_iam_binding" "cloud_run_gcp_master_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.gcp_master_service_json.secret_id
  role      = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.cloud_run_sa.email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "cloud_run_gh_classic_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.gh_classic_pat_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.cloud_run_sa.email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "cloud_run_gh_fine_grained_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.gh_fine_grained_pat_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.cloud_run_sa.email}",
  ]
}

# Allow GitHub Actions to access secrets via Workload Identity Federation
resource "google_secret_manager_secret_iam_binding" "github_actions_gcp_master_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.gcp_master_service_json.secret_id
  role      = "roles/secretmanager.secretAccessor"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/ai-cherry/orchestra-main",
  ]
}

# Token distribution service account
resource "google_service_account" "token_distribution_sa" {
  account_id   = "token-distribution-sa"
  display_name = "Token Distribution Service Account"
  description  = "Service account for distributing short-lived credentials"
}

# Grant token distribution service account access to secrets
resource "google_secret_manager_secret_iam_binding" "token_distribution_access" {
  for_each = toset([
    google_secret_manager_secret.gcp_master_service_json.secret_id,
    google_secret_manager_secret.gh_classic_pat_token.secret_id,
    google_secret_manager_secret.gh_fine_grained_pat_token.secret_id
  ])
  
  project   = var.project_id
  secret_id = each.key
  role      = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.token_distribution_sa.email}",
  ]
}

# Grant token distribution service account token creator role
resource "google_project_iam_member" "token_distribution_token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.token_distribution_sa.email}"
}

# Outputs
output "gcp_master_service_json_secret_id" {
  description = "Secret ID for GCP Master Service JSON"
  value       = google_secret_manager_secret.gcp_master_service_json.secret_id
}

output "gh_classic_pat_token_secret_id" {
  description = "Secret ID for GitHub Classic PAT Token"
  value       = google_secret_manager_secret.gh_classic_pat_token.secret_id
}

output "gh_fine_grained_pat_token_secret_id" {
  description = "Secret ID for GitHub Fine-Grained PAT Token"
  value       = google_secret_manager_secret.gh_fine_grained_pat_token.secret_id
}

output "token_distribution_service_account" {
  description = "Email of the Token Distribution Service Account"
  value       = google_service_account.token_distribution_sa.email
}