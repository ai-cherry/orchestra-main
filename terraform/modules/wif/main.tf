# Terraform module for setting up Workload Identity Federation for GitHub Actions

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_number" {
  description = "The GCP project number"
  type        = string
}

variable "pool_id" {
  description = "The ID for the Workload Identity Pool"
  type        = string
  default     = "github-pool"
}

variable "provider_id" {
  description = "The ID for the Workload Identity Provider"
  type        = string
  default     = "github-provider"
}

variable "service_account_id" {
  description = "The ID for the service account to be used with WIF"
  type        = string
  default     = "github-actions-sa"
}

variable "repository" {
  description = "The GitHub repository in format 'owner/repo'"
  type        = string
  default     = "ai-cherry/orchestra-main"
}

# Create Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = var.pool_id
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
  project                   = var.project_id
}

# Create Workload Identity Provider
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = var.provider_id
  display_name                       = "GitHub Provider"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  project = var.project_id
}

# Create service account for GitHub Actions
resource "google_service_account" "github_actions_sa" {
  account_id   = var.service_account_id
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions deployments"
  project      = var.project_id
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "github_actions_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/storage.admin",
    "roles/artifactregistry.admin",
    "roles/iam.serviceAccountUser"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Allow GitHub Actions to impersonate the service account
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.github_actions_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/projects/${var.project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/attribute.repository/${var.repository}"
  ]
}

# Outputs
output "workload_identity_provider" {
  description = "The full resource name of the Workload Identity Provider"
  value       = "projects/${var.project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id}"
}

output "service_account_email" {
  description = "The email of the service account"
  value       = google_service_account.github_actions_sa.email
}