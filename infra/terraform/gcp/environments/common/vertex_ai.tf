/**
 * Vertex AI resources for Orchestra project
 * Includes Vector Search Index for memory system
 */

# Vector Search Index for memory embeddings
resource "google_vertex_ai_index" "orchestra_memory_index" {
  project     = var.project_id
  region      = "us-west4"
  display_name = "orchestra-memory-index"
  
  description = "Vector index for orchestra memory embeddings"
  
  metadata {
    contents_delta_uri = "gs://${var.project_id}-embeddings/orchestra-memory"
    config {
      dimensions = 768 # Based on embedding model dimension
      approximate_neighbors_count = 20
      distance_measure_type = "DOT_PRODUCT_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }
  
  index_update_method = "STREAM_UPDATE"
  
  labels = {
    managed-by  = "terraform"
    environment = "common"
    purpose     = "vector-search"
  }
}

# Vertex AI Index Endpoint for vector search operations
resource "google_vertex_ai_index_endpoint" "orchestra_memory_endpoint" {
  project      = var.project_id
  region       = "us-west4"
  display_name = "orchestra-memory-endpoint"
  
  description = "Endpoint for orchestra memory vector search"
  
  public_endpoint_enabled = true
  
  labels = {
    managed-by  = "terraform"
    environment = "common"
    purpose     = "vector-search"
  }
}

# Output
output "orchestra_memory_index" {
  value       = google_vertex_ai_index.orchestra_memory_index.id
  description = "ID of the Vertex AI Vector Search Index for orchestra memory"
}

output "orchestra_memory_endpoint" {
  value       = google_vertex_ai_index_endpoint.orchestra_memory_endpoint.id
  description = "ID of the Vertex AI Index Endpoint for orchestra memory"
}
