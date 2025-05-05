/**
 * Storage resources for orchestra project
 * Includes GCS buckets for Terraform state, embeddings, and Artifact Registry
 */

# 1. GCS bucket for Terraform state storage
resource "google_storage_bucket" "terraform_state" {
  name          = "tfstate-cherry-ai-orchestra"
  location      = var.region
  force_destroy = false
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      num_newer_versions = 5
    }
    action {
      type = "Delete"
    }
  }
  
  uniform_bucket_level_access = true
  
  labels = {
    managed-by  = "terraform"
    environment = "common"
    purpose     = "terraform-state"
    project     = "cherry-ai-orchestra"
  }
}

# 2. GCS bucket for embeddings storage
resource "google_storage_bucket" "embeddings_bucket" {
  name          = "${var.project_id}-embeddings"
  location      = "us-west4"
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  labels = {
    managed-by  = "terraform"
    environment = "common"
    purpose     = "vector-embeddings"
  }
}


# Outputs
output "terraform_state_bucket" {
  value       = google_storage_bucket.terraform_state.name
  description = "Name of the GCS bucket for Terraform state"
}

output "embeddings_bucket" {
  value       = google_storage_bucket.embeddings_bucket.name
  description = "Name of the GCS bucket for embeddings storage"
}
