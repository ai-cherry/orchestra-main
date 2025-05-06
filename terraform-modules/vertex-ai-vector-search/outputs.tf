# Outputs for Vertex AI Vector Search Module

output "index_id" {
  description = "The ID of the created Vector Search index"
  value       = google_vertex_ai_index.semantic_memory_index.name
}

output "index_endpoint_id" {
  description = "The ID of the created Vector Search endpoint"
  value       = google_vertex_ai_index_endpoint.semantic_memory_endpoint.name
}

output "deployed_index_id" {
  description = "The ID of the deployed index"
  value       = google_vertex_ai_index_deployed_index.deployed_index.name
}

output "embeddings_bucket" {
  description = "The GCS bucket for storing vector embeddings"
  value       = google_storage_bucket.vector_embeddings.name
}

output "embeddings_bucket_url" {
  description = "The GCS URL for storing vector embeddings"
  value       = "gs://${google_storage_bucket.vector_embeddings.name}"
}

output "index_contents_path" {
  description = "The GCS path for index contents"
  value       = "gs://${google_storage_bucket.vector_embeddings.name}/index-contents"
}

output "endpoint_url" {
  description = "The URL for accessing the Vector Search endpoint"
  value       = "https://${var.region}-aiplatform.googleapis.com/v1/${google_vertex_ai_index_endpoint.semantic_memory_endpoint.name}"
}