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
    "storage-access-key-dev",
    "openrouter-api-key-dev",
    "mistral-api-key-dev",
    "google-api-key-dev",
    "together-ai-api-key-dev",
    "deepseek-api-key-dev",
    "perplexity-api-key-dev",
    "cohere-api-key-dev",
    "huggingface-api-token-dev",
    "portkey-api-key-dev",
    "tavily-api-key-dev",
    "brave-api-key-dev",
    "vertex-api-key-dev",
    "apify-api-token-dev",
    "apollo-io-api-key-dev",
    "exa-api-key-dev",
    "eleven-labs-api-key-dev",
    "external-apis-dev",
    "gcp-client-secret-dev",
    "gcp-service-account-key-dev",
    "oauth-client-secret-dev",
    "certificate-key-dev",
    "alert-webhook-key-dev",
    "monitoring-service-key-dev",
    "service-account-keys-dev",
    "test-data-key-dev",
    "mock-service-key-dev"
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
