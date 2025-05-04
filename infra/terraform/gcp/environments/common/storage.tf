/**
 * Storage resources for cherry-ai-project
 * Includes GCS bucket for Terraform backend and Artifact Registry
 */

# 1. GCS bucket for Terraform state storage
resource "google_storage_bucket" "terraform_state" {
  name          = "tfstate-cherry-ai-project"
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
    project     = "cherry-ai-project"
  }
}

# 2. Artifact Registry Docker repository
resource "google_artifact_registry_repository" "orchestra_images" {
  provider = google-beta
  
  location      = var.region
  repository_id = "orchestra-images"
  description   = "Docker repository for Orchestra application images"
  format        = "DOCKER"
  
  labels = {
    managed-by  = "terraform"
    environment = "common"
    purpose     = "docker-images"
  }
}

# Outputs
output "terraform_state_bucket" {
  value       = google_storage_bucket.terraform_state.name
  description = "Name of the GCS bucket for Terraform state"
}

output "artifact_registry_repository" {
  value       = google_artifact_registry_repository.orchestra_images.name
  description = "Name of the Artifact Registry Docker repository"
}
