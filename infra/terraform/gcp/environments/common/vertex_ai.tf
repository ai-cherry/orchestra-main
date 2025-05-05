/**
 * Vertex AI resources for Orchestra project
 * Includes Vector Search Index for memory system
 */

# Vector Search Index for memory embeddings
resource "google_vertex_ai_index" "orchestra_memory_index" {
  project      = var.project_id
  region       = var.region
  display_name = "${local.env_prefix}-memory-index"
  
  description = "Vector index for orchestra memory embeddings"
  
  metadata {
    contents_delta_uri = "gs://${var.project_id}-embeddings/${local.env_prefix}-memory"
    config {
      dimensions = var.vector_search_dimensions # Based on embedding model dimension
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
  
  labels = merge(local.common_labels, {
    purpose = "vector-search"
  })
  
  # Deployment resource settings
  dedicated_resources {
    machine_spec {
      machine_type = "e2-standard-2"
    }
    min_replica_count = 1
    max_replica_count = 2
  }
}

# Vertex AI Index Endpoint for vector search operations
resource "google_vertex_ai_index_endpoint" "orchestra_memory_endpoint" {
  project      = var.project_id
  region       = var.region
  display_name = "${local.env_prefix}-memory-endpoint"
  
  description = "Endpoint for orchestra memory vector search"
  
  public_endpoint_enabled = true
  
  labels = merge(local.common_labels, {
    purpose = "vector-search"
  })
  
  network = "projects/${var.project_id}/global/networks/default"
  
  # Deployment resource settings
  private_service_connect_config {
    enable_private_service_connect = true
    project_allowlist              = [var.project_id]
  }
}

# Deploy the index to the endpoint
resource "google_vertex_ai_index_endpoint_deployment" "memory_index_deployment" {
  index_endpoint = google_vertex_ai_index_endpoint.orchestra_memory_endpoint.id
  deployed_index {
    index        = google_vertex_ai_index.orchestra_memory_index.id
    display_name = "deployed-memory-index"
    
    dedicated_resources {
      machine_spec {
        machine_type = "e2-standard-2"
      }
      min_replica_count = 1
      max_replica_count = 2
    }
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
