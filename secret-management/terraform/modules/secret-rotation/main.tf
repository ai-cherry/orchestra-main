/**
 * # Secret Rotation Module
 *
 * This module creates the infrastructure needed for automated secret rotation:
 * - Cloud Scheduler job to trigger rotation on a schedule
 * - Cloud Function to execute the rotation logic
 * - Service Account with necessary permissions
 */

# Service account for the rotation function
resource "google_service_account" "rotation_service_account" {
  project      = var.project_id
  account_id   = "secret-rotation-sa-${var.environment}"
  display_name = "Secret Rotation Service Account for ${var.environment}"
  description  = "Service account for automated secret rotation"
}

# Grant Secret Manager Admin role to the service account
resource "google_project_iam_member" "secret_admin" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.rotation_service_account.email}"
}

# Cloud Storage bucket for the function source code
resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-secret-rotation-fn-${var.environment}"
  location = var.region
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Archive the Python function code
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.module}/function"
  output_path = "${path.module}/function/rotation_function.zip"
}

# Upload the archive to Cloud Storage
resource "google_storage_bucket_object" "function_archive" {
  name   = "rotation-function-${data.archive_file.function_zip.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.function_zip.output_path
}

# Create the Cloud Function
resource "google_cloudfunctions_function" "rotation_function" {
  name        = "secret-rotation-function-${var.environment}"
  description = "Automatically rotates secrets in Secret Manager"
  runtime     = "python310"
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_archive.name
  
  entry_point = "rotate_secrets"
  
  # HTTP Trigger
  trigger_http = true
  
  # Environment variables
  environment_variables = {
    PROJECT_ID  = var.project_id
    ENVIRONMENT = var.environment
    SECRETS     = join(",", var.secrets_to_rotate)
  }
  
  # Use the service account
  service_account_email = google_service_account.rotation_service_account.email
  
  # Configure retry on failure
  max_instances = 3
  timeout       = 180
}

# Allow unauthenticated access to the function (if enabled)
resource "google_cloudfunctions_function_iam_member" "invoker" {
  count          = var.allow_unauthenticated ? 1 : 0
  project        = var.project_id
  region         = var.region
  cloud_function = google_cloudfunctions_function.rotation_function.name
  
  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

# Create a service account for Cloud Scheduler
resource "google_service_account" "scheduler_service_account" {
  project      = var.project_id
  account_id   = "secret-scheduler-sa-${var.environment}"
  display_name = "Secret Rotation Scheduler Service Account"
  description  = "Service account for Cloud Scheduler to trigger secret rotation"
}

# Grant the Cloud Scheduler service account permission to invoke the function
resource "google_cloudfunctions_function_iam_member" "scheduler_invoker" {
  project        = var.project_id
  region         = var.region
  cloud_function = google_cloudfunctions_function.rotation_function.name
  
  role   = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${google_service_account.scheduler_service_account.email}"
}

# Create a Cloud Scheduler job to trigger the function
resource "google_cloud_scheduler_job" "rotation_scheduler" {
  name             = "secret-rotation-job-${var.environment}"
  description      = "Triggers the secret rotation function on a schedule"
  schedule         = var.rotation_schedule
  time_zone        = var.time_zone
  attempt_deadline = "320s"
  
  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.rotation_function.https_trigger_url
    
    oidc_token {
      service_account_email = google_service_account.scheduler_service_account.email
    }
  }
}
