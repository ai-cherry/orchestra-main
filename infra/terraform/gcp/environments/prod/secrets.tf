/**
 * Secret Manager configuration for production environment
 * Creates standardized secrets required for the Orchestra application
 */

# Create secrets for the production environment
resource "google_secret_manager_secret" "prod_secrets" {
  for_each = toset([
    "openai-api-key-prod",
    "anthropic-api-key-prod",
    "gemini-api-key-prod",
    "redis-auth-prod",
    "database-password-prod",
    "storage-access-key-prod",
    "openrouter-api-key-prod",
    "mistral-api-key-prod",
    "google-api-key-prod",
    "together-ai-api-key-prod",
    "deepseek-api-key-prod",
    "perplexity-api-key-prod",
    "cohere-api-key-prod",
    "huggingface-api-token-prod",
    "portkey-api-key-prod",
    "tavily-api-key-prod",
    "brave-api-key-prod",
    "vertex-api-key-prod",
    "apify-api-token-prod",
    "apollo-io-api-key-prod",
    "exa-api-key-prod",
    "eleven-labs-api-key-prod",
    "external-apis-prod",
    "gcp-client-secret-prod",
    "gcp-service-account-key-prod",
    "oauth-client-secret-prod",
    "certificate-key-prod",
    "alert-webhook-key-prod",
    "monitoring-service-key-prod",
    "service-account-keys-prod",
    "test-data-key-prod",
    "mock-service-key-prod"
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
resource "google_secret_manager_secret_version" "prod_secret_versions" {
  for_each = google_secret_manager_secret.prod_secrets
  
  secret      = each.value.id
  secret_data = "placeholder-to-be-updated"
}

# Grant access to the orchestra-runner-sa service account
resource "google_secret_manager_secret_iam_binding" "prod_secret_access" {
  for_each  = google_secret_manager_secret.prod_secrets
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
output "prod_secrets" {
  value       = [for secret in google_secret_manager_secret.prod_secrets : secret.name]
  description = "List of created secrets for the production environment"
}
