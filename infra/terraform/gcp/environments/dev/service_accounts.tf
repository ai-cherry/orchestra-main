/**
 * Service accounts for the dev environment
 */

provider "google" {
  project = var.project_id
  region  = var.region
}

# Create a service account for orchestrator testing
resource "google_service_account" "orchestrator_test_sa" {
  account_id   = "orchestrator-test-sa"
  display_name = "Orchestrator Test Service Account"
  description  = "Service account for testing orchestration functionality in dev environment"
}

# Grant necessary IAM roles to the test service account
resource "google_project_iam_member" "test_sa_roles" {
  for_each = toset([
    "roles/datastore.user",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestrator_test_sa.email}"
}

# Reference to outputs
output "orchestrator_test_sa_email" {
  value       = google_service_account.orchestrator_test_sa.email
  description = "Email address of the orchestrator test service account"
}