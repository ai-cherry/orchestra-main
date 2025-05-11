# Service Accounts and IAM Configuration for AI Orchestra
# This file defines the service accounts and IAM permissions needed for deployment

# Service account for Cloud Run services
resource "google_service_account" "cloud_run_service_account" {
  account_id   = "ai-orchestra-service-${var.env}"
  display_name = "AI Orchestra Service Account (${var.env})"
  project      = var.project_id
  description  = "Service account for AI Orchestra Cloud Run services"
}

# Service account for GitHub Actions
resource "google_service_account" "github_actions_service_account" {
  account_id   = "github-actions"
  display_name = "GitHub Actions Service Account"
  project      = var.project_id
  description  = "Service account for GitHub Actions CI/CD"
}

# IAM roles for Cloud Run service account
resource "google_project_iam_binding" "cloud_run_service_account_roles" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:${google_service_account.cloud_run_service_account.email}"
  ]
}

resource "google_project_iam_binding" "cloud_run_storage_role" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  members = ["serviceAccount:${google_service_account.cloud_run_service_account.email}"]
}

resource "google_project_iam_binding" "cloud_run_logging_role" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  members = ["serviceAccount:${google_service_account.cloud_run_service_account.email}"]
}

resource "google_project_iam_binding" "cloud_run_monitoring_role" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  members = ["serviceAccount:${google_service_account.cloud_run_service_account.email}"]
}

resource "google_project_iam_binding" "cloud_run_ai_role" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  members = ["serviceAccount:${google_service_account.cloud_run_service_account.email}"]
}

resource "google_project_iam_binding" "cloud_run_firestore_role" {
  project = var.project_id
  role    = "roles/firestore.user"
  members = ["serviceAccount:${google_service_account.cloud_run_service_account.email}"]
}

# IAM roles for GitHub Actions service account
resource "google_project_iam_binding" "github_actions_run_role" {
  project = var.project_id
  role    = "roles/run.admin"
  members = ["serviceAccount:${google_service_account.github_actions_service_account.email}"]
}

resource "google_project_iam_binding" "github_actions_storage_role" {
  project = var.project_id
  role    = "roles/storage.admin"
  members = ["serviceAccount:${google_service_account.github_actions_service_account.email}"]
}

resource "google_project_iam_binding" "github_actions_artifact_role" {
  project = var.project_id
  role    = "roles/artifactregistry.admin"
  members = ["serviceAccount:${google_service_account.github_actions_service_account.email}"]
}

resource "google_project_iam_binding" "github_actions_secret_role" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  members = ["serviceAccount:${google_service_account.github_actions_service_account.email}"]
}

resource "google_project_iam_binding" "github_actions_sa_user_role" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  members = ["serviceAccount:${google_service_account.github_actions_service_account.email}"]
}

# Secret for service account key
resource "google_secret_manager_secret" "service_account_key" {
  secret_id = "ai-orchestra-service-account"
  project   = var.project_id
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# Create service account key and store in Secret Manager
resource "google_service_account_key" "cloud_run_service_account_key" {
  service_account_id = google_service_account.cloud_run_service_account.name
  key_algorithm      = "KEY_ALG_RSA_2048"
  public_key_type    = "TYPE_X509_PEM_FILE"
}

resource "google_secret_manager_secret_version" "service_account_key_version" {
  secret      = google_secret_manager_secret.service_account_key.id
  secret_data = base64decode(google_service_account_key.cloud_run_service_account_key.private_key)
}

# Output the service account emails
output "github_service_account_email" {
  value       = google_service_account.github_actions_service_account.email
  description = "Service Account Email for GitHub Actions"
}

output "cloud_run_service_account_email" {
  value       = google_service_account.cloud_run_service_account.email
  description = "Service Account Email for Cloud Run services"
}