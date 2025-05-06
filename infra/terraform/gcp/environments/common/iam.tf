/**
 * IAM Configuration for the Orchestra project
 */

# Workload Identity Federation pool for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Identity Pool"
  description               = "Identity pool for GitHub Actions workflows"
  
  disabled = false
  
  # Note: labels are not supported in the current provider version
  # labels = local.common_labels
}

# GitHub provider for Workload Identity Federation
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"
  description                        = "Workload Identity Federation provider for GitHub Actions"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.owner"      = "assertion.repository_owner"
    "attribute.workflow"   = "assertion.workflow"
    "attribute.ref"        = "assertion.ref"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_condition = "attribute.repository == \"${var.github_repo}\""
}

# Service Account for GitHub Actions deployments
resource "google_service_account" "github_actions_deployer" {
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions Deployer SA"
  description  = "Service account used by GitHub Actions to deploy the Orchestra application"
  project      = var.project_id
}

# Service Account for Orchestra Cloud Run services
resource "google_service_account" "orchestra_runner_sa" {
  account_id   = "orchestra-runner-sa"
  display_name = "Orchestra Cloud Run Runtime SA"
  description  = "Service account used by Orchestra services running in Cloud Run"
  project      = var.project_id
}

# Allow the GitHub Actions to impersonate the service account via Workload Identity Federation
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.github_actions_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}"
  ]
}

# Grant necessary deployment roles to the GitHub Actions deployer service account
resource "google_project_iam_member" "github_actions_deployer_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.writer",
    "roles/secretmanager.admin",
    "roles/editor",  # Broader role for setup flexibility - should be refined later
    "roles/storage.admin",
    "roles/cloudtasks.admin",
    "roles/pubsub.admin",
    "roles/redis.admin",
    "roles/aiplatform.admin"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_actions_deployer.email}"
}

# Grant necessary runtime roles to the Orchestra Runner service account
resource "google_project_iam_member" "orchestra_runner_sa_roles" {
  for_each = toset([
    "roles/datastore.user",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/redis.viewer",
    "roles/pubsub.subscriber",
    "roles/cloudtasks.enqueuer",
    "roles/storage.objectViewer"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestra_runner_sa.email}"
}

# Outputs moved to outputs.tf
