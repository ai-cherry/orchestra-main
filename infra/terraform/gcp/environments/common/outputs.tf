/**
 * Consolidated outputs for the common environment
 * This file centralizes all outputs from various resource files
 */

# IAM Outputs
output "github_actions_deployer_email" {
  value       = google_service_account.github_actions_deployer.email
  description = "Email address of the GitHub Actions deployer service account"
}

output "orchestra_runner_sa_email" {
  value       = google_service_account.orchestra_runner_sa.email
  description = "Email address of the Orchestra Cloud Run service account"
}

output "workload_identity_provider" {
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  description = "Full resource name of the Workload Identity provider"
}

# Storage Outputs
output "terraform_state_bucket" {
  value       = google_storage_bucket.terraform_state.name
  description = "Name of the GCS bucket for Terraform state"
}

output "embeddings_bucket" {
  value       = google_storage_bucket.embeddings_bucket.name
  description = "Name of the GCS bucket for embeddings storage"
}

# Artifact Registry Outputs
output "cherry_ai_artifact_registry_repository" {
  value       = google_artifact_registry_repository.cherry_ai_orchestra_images.name
  description = "Name of the Artifact Registry Docker repository for orchestra"
}

# Database Outputs
output "firestore_database_id" {
  value       = module.firestore.database_id
  description = "ID of the Firestore database in Native mode"
}

# Redis Outputs
output "redis_host" {
  value       = google_redis_instance.orchestra-redis-cache.host
  description = "The IP address of the Redis instance"
}

output "redis_port" {
  value       = google_redis_instance.orchestra-redis-cache.port
  description = "The port of the Redis instance"
}

# Vertex AI Outputs
output "orchestra_memory_index" {
  value       = google_vertex_ai_index.orchestra_memory_index.id
  description = "ID of the Vertex AI Vector Search Index for orchestra memory"
}

output "orchestra_memory_endpoint" {
  value       = google_vertex_ai_index_endpoint.orchestra_memory_endpoint.id
  description = "ID of the Vertex AI Index Endpoint for orchestra memory"
}

# Secret Manager Outputs
output "openai_secret_id" {
  value       = google_secret_manager_secret.openai_api_key.id
  description = "ID of the OpenAI API key secret"
}

output "anthropic_secret_id" {
  value       = google_secret_manager_secret.anthropic_api_key.id
  description = "ID of the Anthropic API key secret"
}

output "redis_auth_secret_id" {
  value       = google_secret_manager_secret.redis_auth.id
  description = "ID of the Redis authentication string secret"
}

# Pub/Sub Outputs
output "pubsub_topic_id" {
  value       = google_pubsub_topic.orchestra_events.id
  description = "ID of the Orchestra Pub/Sub events topic"
}

# Cloud Tasks Outputs
output "tasks_queue_id" {
  value       = google_cloud_tasks_queue.orchestra_tasks_queue.id
  description = "ID of the Orchestra Cloud Tasks queue"
}