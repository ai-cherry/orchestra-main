/**
* Service accounts for the dev environment
 */

# Test service account for CI/CD pipelines
resource "google_service_account" "orchestrator_test_sa" {
  account_id   = "orchestrator-test-sa"
  display_name = "Orchestrator Test Service Account"
  description  = "Service account for testing the Orchestra application"
}

# Grant necessary permissions to the test service account
resource "google_project_iam_member" "orchestrator_test_sa_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/firestore.user",
    "roles/aiplatform.user",
    "roles/storage.objectUser",
    "roles/logging.logWriter"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestrator_test_sa.email}"
}

# Output the test service account email for use in CI/CD workflows
output "orchestrator_test_sa_email" {
  value       = google_service_account.orchestrator_test_sa.email
  description = "Email address of the Orchestrator test service account"
}

# Runner service account for Cloud Run services
resource "google_service_account" "orchestra_runner_sa" {
  account_id   = "orchestra-runner-sa"
  display_name = "Orchestra Runner Service Account"
  description  = "Service account for running Orchestra services in Cloud Run"
}

# Grant necessary permissions to the runner service account
resource "google_project_iam_member" "orchestra_runner_sa_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/firestore.user",
    "roles/aiplatform.user",
    "roles/storage.objectUser",
    "roles/logging.logWriter"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestra_runner_sa.email}"
}

# Output the runner service account email
output "orchestra_runner_sa_email" {
  value       = google_service_account.orchestra_runner_sa.email
  description = "Email address of the Orchestra runner service account"
}
