# Service Accounts for AI Orchestra Development Environment

# Orchestrator Test Service Account
resource "google_service_account" "orchestrator_test_sa" {
  account_id   = "orchestrator-test-sa"
  display_name = "Orchestrator Test Service Account"
  description  = "Service account for testing orchestrator functionality in the development environment"
  project      = var.project_id
}

# Grant necessary roles to the Orchestrator Test Service Account
resource "google_project_iam_member" "orchestrator_test_sa_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/firestore.user",
    "roles/redis.editor"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestrator_test_sa.email}"
}

# Orchestra Runner Service Account (if not already created elsewhere)
resource "google_service_account" "orchestra_runner_sa" {
  account_id   = "orchestra-runner-sa"
  display_name = "Orchestra Runner Service Account"
  description  = "Service account for running AI Orchestra services in Cloud Run"
  project      = var.project_id
}

# Grant necessary roles to the Orchestra Runner Service Account
resource "google_project_iam_member" "orchestra_runner_sa_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/firestore.user",
    "roles/redis.editor"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestra_runner_sa.email}"
}