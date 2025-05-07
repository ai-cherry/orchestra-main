variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

variable "index_replicas" {
  description = "Number of replicas for the vector index"
  type        = number
  default     = 1
}

variable "vector_dimension" {
  description = "Dimensionality of the vector embeddings"
  type        = number
  default     = 1536
}

# Enable the Vertex AI API
resource "google_project_service" "vertex_ai" {
  project = var.project_id
  service = "aiplatform.googleapis.com"
  
  # Don't disable the API if the resource is destroyed
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Create a Cloud Storage bucket for vector search index data
resource "google_storage_bucket" "vector_index_bucket" {
  name     = "agi-baby-cherry-vector-${var.env}"
  location = var.region
  force_destroy = var.env != "prod"  # Allow force destroy for non-prod environments
  
  # Add versioning for prod environments
  dynamic "versioning" {
    for_each = var.env == "prod" ? [1] : []
    content {
      enabled = true
    }
  }
  
  # Lifecycle rules for cost optimization
  lifecycle_rule {
    condition {
      age = 30  # 30 days
    }
    action {
      type = "Delete"
    }
  }
  
  # Add uniform bucket-level access
  uniform_bucket_level_access = true
}

# Define the Vertex AI vector search index using the google-beta provider
resource "google_vertex_ai_index" "vector_index" {
  provider    = google-beta
  region      = var.region
  display_name = "orchestra-embeddings-${var.env}"
  
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.vector_index_bucket.name}/vector-index/"
    config {
      dimensions = var.vector_dimension  # Vector dimension
      approximate_neighbors_count = 20   # Top-k for search
      distance_measure_type = "COSINE"
      shard_size = "SHARD_SIZE_SMALL"    # Optimize for latency (<10ms)
    }
  }
  
  index_update_method = "BATCH_UPDATE"
  
  # Remove the unsupported blocks and convert to supported format or annotations
  # The replica count and machine type can be set through other supported parameters
  # or may need to be configured through a different resource
  
  depends_on = [google_project_service.vertex_ai]
}

# Create a dedicated service account for Vertex AI operations
resource "google_service_account" "vertex_service_account" {
  account_id   = "vertex-ai-${var.env}-sa"
  display_name = "Vertex AI ${var.env} Service Account"
  description  = "Service account for Vertex AI operations in ${var.env}"
}

# Grant necessary IAM roles
resource "google_project_iam_member" "vertex_sa_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vertex_service_account.email}"
}

resource "google_project_iam_member" "vertex_sa_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.vertex_service_account.email}"
}

# Grant service account access to the bucket
resource "google_storage_bucket_iam_member" "vector_bucket_access" {
  bucket = google_storage_bucket.vector_index_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.vertex_service_account.email}"
}

output "index_id" {
  value = google_vertex_ai_index.vector_index.id
}

output "vector_bucket" {
  value = google_storage_bucket.vector_index_bucket.name
}

output "service_account" {
  value = google_service_account.vertex_service_account.email
}
