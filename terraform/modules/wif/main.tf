# Terraform module for setting up Workload Identity Federation for GitHub Actions
# This module creates the necessary resources for WIF authentication in GCP

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
  default     = "ai-cherry"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "orchestra-main"
}

variable "pool_id" {
  description = "Workload Identity Pool ID"
  type        = string
  default     = "github-actions-pool"
}

variable "provider_id" {
  description = "Workload Identity Provider ID"
  type        = string
  default     = "github-actions-provider"
}

variable "service_accounts" {
  description = "Map of service accounts to create with their roles"
  type        = map(list(string))
  default     = {
    "orchestrator-api"   = ["roles/run.admin", "roles/secretmanager.secretAccessor", "roles/firestore.user"]
    "phidata-agent-ui"   = ["roles/run.admin", "roles/secretmanager.secretAccessor"]
    "github-actions"     = ["roles/artifactregistry.writer", "roles/run.admin", "roles/secretmanager.secretAccessor", "roles/storage.admin"]
    "codespaces-dev"     = ["roles/viewer", "roles/secretmanager.secretAccessor", "roles/logging.viewer"]
  }
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "iamcredentials.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "secretmanager.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  
  project = var.project_id
  service = each.value
  
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Create Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  project                   = var.project_id
  workload_identity_pool_id = var.pool_id
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions workflows"
  
  depends_on = [google_project_service.required_apis]
}

# Create Workload Identity Provider
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = var.provider_id
  display_name                       = "GitHub Provider"
  
  attribute_mapping = {
    "google.subject"           = "assertion.sub"
    "attribute.actor"          = "assertion.actor"
    "attribute.repository"     = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Create service accounts
resource "google_service_account" "service_accounts" {
  for_each     = var.service_accounts
  project      = var.project_id
  account_id   = each.key
  display_name = "${each.key} for WIF"
  
  depends_on = [google_project_service.required_apis]
}

# Grant roles to service accounts
resource "google_project_iam_member" "service_account_roles" {
  for_each = {
    for pair in flatten([
      for sa_name, roles in var.service_accounts : [
        for role in roles : {
          sa_name = sa_name
          role    = role
        }
      ]
    ]) : "${pair.sa_name}-${pair.role}" => pair
  }
  
  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.service_accounts[each.value.sa_name].email}"
}

# Configure Workload Identity Federation for service accounts
resource "google_service_account_iam_binding" "wif_binding" {
  for_each           = var.service_accounts
  service_account_id = google_service_account.service_accounts[each.key].name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_org}/${var.github_repo}"
  ]
}

# Outputs
output "workload_identity_provider" {
  description = "Workload Identity Provider resource name"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "service_account_emails" {
  description = "Map of service account names to their emails"
  value       = {
    for sa_name, sa in google_service_account.service_accounts : sa_name => sa.email
  }
}

output "github_actions_service_account" {
  description = "Service account for GitHub Actions"
  value       = google_service_account.service_accounts["github-actions"].email
}