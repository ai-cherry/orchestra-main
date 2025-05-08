# Performance-optimized Vertex AI configuration for AI Orchestra

# Vertex AI Endpoint for Embeddings
resource "google_vertex_ai_endpoint" "embedding_endpoint" {
  name         = "embedding-endpoint-${var.env}"
  location     = var.region
  display_name = "Embedding Endpoint ${var.env}"
}

# Vertex AI Model for Embeddings
resource "google_vertex_ai_model" "embedding_model" {
  name         = "embedding-model-${var.env}"
  location     = var.region
  display_name = "Embedding Model ${var.env}"
  
  artifact_uri = "gs://${var.project_id}-model-artifacts-${var.env}/embedding-model"
  
  container_spec {
    image_uri = "us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-8:latest"
  }
}

# Vertex AI Model Deployment
resource "google_vertex_ai_model_deployment" "embedding_model_deployment" {
  name         = "embedding-model-deployment-${var.env}"
  location     = var.region
  display_name = "Embedding Model Deployment ${var.env}"
  
  endpoint     = google_vertex_ai_endpoint.embedding_endpoint.id
  model        = google_vertex_ai_model.embedding_model.id
  
  dedicated_resources {
    machine_spec {
      machine_type = "n1-highmem-8"
    }
    
    min_replica_count = 1
    max_replica_count = 10
  }
  
  depends_on = [
    google_vertex_ai_endpoint.embedding_endpoint
  ]
}

# Outputs
output "embedding_endpoint_id" {
  description = "The ID of the Vertex AI Embedding Endpoint"
  value       = google_vertex_ai_endpoint.embedding_endpoint.id
}

output "embedding_model_id" {
  description = "The ID of the Vertex AI Embedding Model"
  value       = google_vertex_ai_model.embedding_model.id
}