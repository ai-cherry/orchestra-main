/**
 * # Memory Infrastructure Module Outputs
 *
 * This file defines the outputs for the memory infrastructure module.
 */

output "redis_host" {
  description = "The IP address of the Redis instance"
  value       = google_redis_instance.short_term_memory.host
}

output "redis_port" {
  description = "The port of the Redis instance"
  value       = google_redis_instance.short_term_memory.port
}

output "redis_password_secret" {
  description = "The Secret Manager secret ID for the Redis password"
  value       = google_secret_manager_secret.redis_password.secret_id
}

output "redis_instance_id" {
  description = "The ID of the Redis instance"
  value       = google_redis_instance.short_term_memory.id
}

output "redis_instance_name" {
  description = "The name of the Redis instance"
  value       = google_redis_instance.short_term_memory.name
}

output "vector_search_index" {
  description = "The ID of the Vertex AI Vector Search index"
  value       = google_vertex_ai_index.semantic_memory.name
}

output "vector_search_endpoint" {
  description = "The ID of the Vertex AI Vector Search endpoint"
  value       = google_vertex_ai_index_endpoint.semantic_memory_endpoint.name
}

output "vector_search_endpoint_url" {
  description = "The URL of the Vertex AI Vector Search endpoint"
  value       = "https://${var.region}-aiplatform.googleapis.com/v1/${google_vertex_ai_index_endpoint.semantic_memory_endpoint.name}"
}

output "firestore_collections" {
  description = "The Firestore collections created for memory storage"
  value       = var.firestore_collections
}

output "memory_config" {
  description = "Configuration for the memory system"
  value = {
    redis = {
      host           = google_redis_instance.short_term_memory.host
      port           = google_redis_instance.short_term_memory.port
      password_secret = google_secret_manager_secret.redis_password.secret_id
    }
    firestore = {
      project_id     = var.project_id
      collections    = var.firestore_collections
    }
    vertex = {
      project_id     = var.project_id
      region         = var.region
      index_name     = google_vertex_ai_index.semantic_memory.name
      endpoint_name  = google_vertex_ai_index_endpoint.semantic_memory_endpoint.name
      vector_dimension = var.vector_dimension
    }
  }
}