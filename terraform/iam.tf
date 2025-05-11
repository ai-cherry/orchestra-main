# IAM configuration for AI Orchestra
# This file contains all IAM-related resources including service accounts and permissions

# Create a service account for Cloud Run
resource "google_service_account" "cloud_run_service_account" {
  account_id   = "${var.service_account_name}-${var.env}-sa"
  display_name = "AI Orchestra ${var.env} Service Account"
  description  = "Service account for AI Orchestra Cloud Run service"
}

# Grant necessary logging and monitoring permissions to the service account
resource "google_project_iam_member" "cloud_run_basic_permissions" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Grant Firestore access to the service account
resource "google_project_iam_member" "firestore_access" {
  project = var.project_id
  role    = "roles/firestore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Grant Vertex AI access to the service account
resource "google_project_iam_member" "vertex_ai_access" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Create Secret Manager secret for service account key
resource "google_secret_manager_secret" "secret_management_key" {
  secret_id = "${var.secret_name_prefix}-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Create initial secret version with placeholder data
resource "google_secret_manager_secret_version" "initial_version" {
  secret      = google_secret_manager_secret.secret_management_key.id
  secret_data = "placeholder-to-be-updated-by-deployment-script"
}

# Grant secret access to the service account (scoped to specific secret)
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.secret_management_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# IAM policy to make the service publicly accessible
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}