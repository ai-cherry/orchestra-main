/**
 * Secret Manager configuration for dev environment
 * Creates standardized secrets required for the Orchestra application
 */

# Create secrets for the dev environment
resource "google_secret_manager_secret" "dev_secrets" {
  for_each = toset([
    "openai-api-key-dev",
    "anthropic-api-key-dev",
    "gemini-api-key-dev", 
    "redis-auth-dev",
    "database-password-dev",
    "storage-access-key-dev"
  ])
  
  project   = var.project_id
  secret_id = each.key
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.env
    managed-by  = "terraform"
  }
}

# Create empty versions for each secret (to be populated manually)
resource "google_secret_manager_secret_version" "dev_secret_versions" {
  for_each = google_secret_manager_secret.dev_secrets
  
  secret      = each.value.id
  secret_data = "placeholder-to-be-updated"
}

# Grant access to the orchestra-runner-sa service account
resource "google_secret_manager_secret_iam_binding" "dev_secret_access" {
  for_each  = google_secret_manager_secret.dev_secrets
  project   = var.project_id
  secret_id = each.value.name
  role      = "roles/secretmanager.secretAccessor"
  members   = [
    "serviceAccount:${data.google_service_account.orchestra_runner_sa.email}"
  ]
}

# Reference the orchestra-runner-sa service account
data "google_service_account" "orchestra_runner_sa" {
  account_id = "orchestra-runner-sa"
}

# Output the list of created secrets
output "dev_secrets" {
  value       = [for secret in google_secret_manager_secret.dev_secrets : secret.name]
  description = "List of created secrets for the dev environment"
}
