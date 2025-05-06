/**
 * Orchestra IAM Permissions Management
 * 
 * This configuration manages IAM permissions for administrators and developers.
 * It handles role assignments for Secret Manager, Compute, and other GCP services.
 */

# Variable for Secret Manager Administrators 
variable "secret_manager_admins" {
  description = "List of users who should have Secret Manager Admin role"
  type        = list(string)
  default     = []  # Empty by default for safety; specify in tfvars
}

# Grant Secret Manager Admin role to specified users
resource "google_project_iam_member" "secret_manager_admin_users" {
  for_each = toset(var.secret_manager_admins)
  
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "user:${each.value}"
  
  depends_on = [google_project_service.required_apis]
}

# Service Account for CI/CD with Secret Manager admin permissions
resource "google_service_account" "cicd_secret_manager" {
  account_id   = "cicd-secret-manager-${var.env}"
  display_name = "CI/CD Secret Manager Administrator"
  description  = "Service account for CI/CD pipelines that need to manage secrets"
}

# Grant Secret Manager Admin role to the CI/CD service account
resource "google_project_iam_member" "cicd_secret_manager_admin" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.cicd_secret_manager.email}"
  
  depends_on = [google_service_account.cicd_secret_manager]
}

# Output the CI/CD service account email for use in CI/CD pipelines
output "cicd_secret_manager_email" {
  description = "Email of the service account for CI/CD pipelines with Secret Manager admin permissions"
  value       = google_service_account.cicd_secret_manager.email
}