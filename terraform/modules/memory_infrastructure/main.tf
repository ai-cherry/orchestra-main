/**
 * # Memory Infrastructure Module
 *
 * This module provisions the necessary GCP resources for the AI Orchestra memory system:
 * - Redis instance for short-term memory
 * - Firestore database for mid/long-term memory
 * - Vertex AI Vector Search for semantic memory
 * - Secret Manager for storing credentials
 */

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "redis.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_on_destroy = false
}

# Generate a random password for Redis
resource "random_password" "redis_password" {
  length  = 16
  special = true
}

# Store Redis password in Secret Manager
resource "google_secret_manager_secret" "redis_password" {
  project   = var.project_id
  secret_id = "redis-password"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "redis_password" {
  secret      = google_secret_manager_secret.redis_password.id
  secret_data = random_password.redis_password.result
}

# Create Redis instance for short-term memory
resource "google_redis_instance" "short_term_memory" {
  name           = "orchestra-short-term-memory"
  project        = var.project_id
  region         = var.region
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb
  
  auth_enabled = true

  redis_version = "REDIS_6_X"
  
  # Use a custom display name
  display_name = "AI Orchestra Short-Term Memory"
  
  # Set labels for better organization
  labels = {
    environment = var.environment
    application = "ai-orchestra"
    component   = "memory"
    type        = "short-term"
  }

  depends_on = [google_project_service.required_apis]
}

# Create Firestore database for mid/long-term memory
# Note: Firestore is a project-level resource and can only be created once per project
# This resource is commented out because it's likely that Firestore is already enabled
# Uncomment if you need to create a new Firestore database
/*
resource "google_firestore_database" "memory_database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}
*/

# Create Vertex AI Vector Search index for semantic memory
resource "google_vertex_ai_index" "semantic_memory" {
  provider = google-beta
  project  = var.project_id
  region   = var.region
  
  display_name = "orchestra-semantic-memory"
  description  = "AI Orchestra Semantic Memory Index"
  
  metadata {
    contents_delta_uri = "gs://${var.storage_bucket}/semantic-memory"
    config {
      dimensions                 = var.vector_dimension
      approximate_neighbors_count = 150
      distance_measure_type      = "DOT_PRODUCT_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 500
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }

  index_update_method = "BATCH_UPDATE"

  depends_on = [google_project_service.required_apis]
}

# Create Vertex AI Vector Search endpoint
resource "google_vertex_ai_index_endpoint" "semantic_memory_endpoint" {
  provider = google-beta
  project  = var.project_id
  region   = var.region
  
  display_name = "orchestra-semantic-memory-endpoint"
  description  = "AI Orchestra Semantic Memory Endpoint"
  
  network      = var.network
  
  private_service_connect_config {
    enable_private_service_connect = true
    project_allowlist              = [var.project_id]
  }

  depends_on = [google_project_service.required_apis]
}

# Deploy the index to the endpoint
resource "google_vertex_ai_index_endpoint_iam_member" "semantic_memory_endpoint_iam" {
  provider = google-beta
  project  = var.project_id
  region   = var.region
  
  index_endpoint = google_vertex_ai_index_endpoint.semantic_memory_endpoint.name
  role           = "roles/aiplatform.user"
  member         = "serviceAccount:${var.service_account_email}"

  depends_on = [google_vertex_ai_index_endpoint.semantic_memory_endpoint]
}

# Create IAM bindings for the service account
resource "google_project_iam_member" "service_account_bindings" {
  for_each = toset([
    "roles/redis.editor",
    "roles/datastore.user",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${var.service_account_email}"
}

# Output the Redis connection information
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

# Output the Vertex AI Vector Search information
output "vector_search_index" {
  description = "The ID of the Vertex AI Vector Search index"
  value       = google_vertex_ai_index.semantic_memory.name
}

output "vector_search_endpoint" {
  description = "The ID of the Vertex AI Vector Search endpoint"
  value       = google_vertex_ai_index_endpoint.semantic_memory_endpoint.name
}