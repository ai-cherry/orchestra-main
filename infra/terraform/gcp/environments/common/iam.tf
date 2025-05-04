/**
 * IAM resources for the cherry-ai-project
 * Includes Workload Identity Federation for GitHub Actions and Service Accounts
 */

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Create Workload Identity Pool for GitHub
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Pool"
  description               = "Identity pool for GitHub Actions workflows"
}

# 2. Create Workload Identity Provider for GitHub
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# 3. Create GitHub Actions Deployer Service Account
resource "google_service_account" "github_actions_deployer" {
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions Deployer SA"
  description  = "Service account for GitHub Actions deployments"
}

# 4. Create Orchestra Cloud Run Runtime Service Account
resource "google_service_account" "orchestra_runner_sa" {
  account_id   = "orchestra-runner-sa"
  display_name = "Orchestra Cloud Run Runtime SA"
  description  = "Service account for Orchestra Cloud Run services"
}

# 5. Allow GitHub Actions to impersonate the Service Account
resource "google_service_account_iam_binding" "github_workload_identity_binding" {
  service_account_id = google_service_account.github_actions_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/ai-cherry/orchestra-main"
  ]
}

# 6. Grant necessary permissions to GitHub Actions Deployer SA
resource "google_project_iam_member" "github_actions_deployer_roles" {
  for_each = toset([
    "roles/run.admin",              # Manage Cloud Run services
    "roles/storage.admin",          # Manage storage (for artifacts)
    "roles/iam.serviceAccountUser", # Use service accounts
    "roles/artifactregistry.writer", # Push to Artifact Registry
    "roles/secretmanager.admin",    # Manage secrets
    "roles/editor"                  # Temporary broad permissions for initial setup
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_actions_deployer.email}"
}

# 7. Grant necessary permissions to Orchestra Runner SA
resource "google_project_iam_member" "orchestra_runner_sa_roles" {
  for_each = toset([
    "roles/logging.logWriter",           # Write logs
    "roles/monitoring.metricWriter",     # Write metrics
    "roles/secretmanager.secretAccessor", # Access secrets
    "roles/aiplatform.user",             # Use Vertex AI
    "roles/datastore.user",              # Access Datastore/Firestore
    "roles/cloudtrace.agent"             # Write trace data
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestra_runner_sa.email}"
}

# 8. Grant the github-actions-deployer SA workload identity permission
resource "google_project_iam_member" "github_actions_workload_identity" {
  project = var.project_id
  role    = "roles/iam.workloadIdentityUser"
  member  = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/ai-cherry/orchestra-main"
}

# 9. Outputs
output "workload_identity_pool_name" {
  value       = google_iam_workload_identity_pool.github_pool.name
  description = "The full resource name of the Workload Identity Pool"
}

output "workload_identity_pool_provider_name" {
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  description = "The full resource name of the Workload Identity Pool Provider"
}

output "github_actions_deployer_email" {
  value       = google_service_account.github_actions_deployer.email
  description = "Email of the GitHub Actions deployer service account"
}

output "orchestra_runner_sa_email" {
  value       = google_service_account.orchestra_runner_sa.email
  description = "Email of the Orchestra Cloud Run runtime service account"
}
