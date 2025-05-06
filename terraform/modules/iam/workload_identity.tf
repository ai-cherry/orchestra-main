/**
 * Workload Identity Federation for Secure CI/CD Deployments
 * 
 * This Terraform module sets up Workload Identity Federation to securely authenticate 
 * CI/CD pipelines with Google Cloud Platform, eliminating the need for 
 * long-lived service account keys.
 */

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "pool_id" {
  description = "Workload Identity Pool ID"
  type        = string
  default     = "github-actions-pool"
}

variable "provider_id" {
  description = "Workload Identity Provider ID"
  type        = string
  default     = "github-provider"
}

variable "github_organization" {
  description = "GitHub organization name"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository name"
  type        = string
}

variable "service_account_id" {
  description = "Service account ID for Terraform deployments"
  type        = string
  default     = "terraform-deployer"
}

# Workload Identity Pool
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = var.pool_id
  display_name             = "GitHub Actions Pool"
  description              = "Identity pool for GitHub Actions CI/CD workflows"
  project                  = var.project_id
}

# Workload Identity Provider
resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.id
  workload_identity_pool_provider_id = var.provider_id
  display_name                       = "GitHub Actions Provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.workflow"   = "assertion.workflow"
    "attribute.ref"        = "assertion.ref"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Service Account for Terraform Deployments
resource "google_service_account" "terraform_deployer" {
  account_id   = var.service_account_id
  display_name = "Terraform Deployment Service Account"
  description  = "Service account used for automated Terraform deployments"
  project      = var.project_id
}

# IAM Binding for Workload Identity Federation
resource "google_service_account_iam_binding" "terraform_workload_identity" {
  service_account_id = google_service_account.terraform_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_organization}/${var.github_repository}"
  ]
}

# Project IAM bindings for the service account
resource "google_project_iam_member" "terraform_deployer_roles" {
  for_each = toset([
    "roles/compute.admin",
    "roles/container.admin",
    "roles/iam.serviceAccountUser",
    "roles/storage.admin",
    "roles/secretmanager.secretAccessor",
    "roles/cloudsql.admin"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

# Optional: Secret for storing GitHub tokens or other credentials
resource "google_secret_manager_secret" "github_token" {
  secret_id = "github-token"
  project   = var.project_id
  
  replication {
    automatic = true
  }
}

# Access binding for the secret
resource "google_secret_manager_secret_iam_member" "github_token_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.github_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

# Outputs
output "workload_identity_provider" {
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "The full resource name of the Workload Identity Provider"
}

output "service_account_email" {
  value       = google_service_account.terraform_deployer.email
  description = "Email of the service account for Terraform deployments"
}

output "setup_instructions" {
  value = <<-EOT
    To use Workload Identity Federation in GitHub Actions:
    
    1. Add the following to your GitHub workflow:
    
    ```yaml
    jobs:
      deploy:
        # ...
        permissions:
          contents: 'read'
          id-token: 'write'
        
        steps:
          - uses: 'actions/checkout@v3'
          
          - id: 'auth'
            uses: 'google-github-actions/auth@v1'
            with:
              workload_identity_provider: '${google_iam_workload_identity_pool_provider.github.name}'
              service_account: '${google_service_account.terraform_deployer.email}'
          
          # Continue with Terraform or other deployment steps
    ```
    
    2. The authenticated workflow will use the service account ${google_service_account.terraform_deployer.email}
    3. This service account has permissions for: compute, container, IAM, storage, Secret Manager, and Cloud SQL
  EOT
  description = "Instructions for setting up Workload Identity in GitHub Actions"
}
