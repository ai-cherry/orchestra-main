# Vertex AI Vector Search Module
# This module creates a Vector Search index for semantic memory

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

resource "google_project_service" "vertex_ai" {
  project = var.project_id
  service = "aiplatform.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

resource "google_storage_bucket" "vector_embeddings" {
  name     = "${var.project_id}-vector-embeddings"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = var.force_destroy_bucket

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.vertex_ai]
}

resource "google_vertex_ai_index" "semantic_memory_index" {
  project     = var.project_id
  region      = var.region
  display_name = "${var.index_name_prefix}-semantic-memory"
  
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.vector_embeddings.name}/index-contents"
    config {
      dimensions = var.embedding_dimensions
      approximate_neighbors_count = var.approximate_neighbors_count
      distance_measure_type = var.distance_measure_type
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = var.leaf_node_embedding_count
          leaf_nodes_to_search_percent = var.leaf_nodes_to_search_percent
        }
      }
    }
  }

  index_update_method = "BATCH_UPDATE"
  
  depends_on = [google_project_service.vertex_ai]
}

resource "google_vertex_ai_index_endpoint" "semantic_memory_endpoint" {
  project     = var.project_id
  region      = var.region
  display_name = "${var.index_name_prefix}-semantic-memory-endpoint"
  
  network     = var.network_id != "" ? var.network_id : null
  
  depends_on = [google_project_service.vertex_ai]
}

resource "google_vertex_ai_index_endpoint_iam_binding" "public_access" {
  project = var.project_id
  region  = var.region
  index_endpoint = google_vertex_ai_index_endpoint.semantic_memory_endpoint.name
  role    = "roles/aiplatform.indexEndpointUser"
  members = [
    "serviceAccount:${var.service_account_email}"
  ]
}

resource "google_vertex_ai_index_deployed_index" "deployed_index" {
  project      = var.project_id
  region       = var.region
  index_endpoint = google_vertex_ai_index_endpoint.semantic_memory_endpoint.name
  deployed_index_id = "${var.index_name_prefix}-deployed"
  display_name  = "${var.index_name_prefix}-deployed"
  index        = google_vertex_ai_index.semantic_memory_index.name
  
  dedicated_resources {
    machine_spec {
      machine_type = var.machine_type
    }
    min_replica_count = var.min_replica_count
    max_replica_count = var.max_replica_count
  }
}