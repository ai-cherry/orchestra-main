/**
 * Storage resources for orchestra project
 * Includes GCS buckets for Terraform state, embeddings, and Artifact Registry
 */

# 1. GCS bucket for Terraform state storage
resource "google_storage_bucket" "terraform_state" {
  name          = "tfstate-cherry-ai-orchestra"
  location      = var.region
  force_destroy = false
  project       = var.project_id
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      num_newer_versions = 5
      age = 30  # Archive versions older than 30 days
    }
    action {
      type = "Delete"
    }
  }
  
  uniform_bucket_level_access = true
  
  # Enable object versioning and retention
  retention_policy {
    is_locked = false
    retention_period = 2592000  # 30 days in seconds
  }
  
  # Enable encryption with CMEK (optional)
  encryption {
    default_kms_key_name = null  # Use Google-managed key for now
  }
  
  labels = merge(local.common_labels, {
    purpose = "terraform-state"
    project = "cherry-ai-orchestra"
  })
}

# 2. GCS bucket for embeddings storage
resource "google_storage_bucket" "embeddings_bucket" {
  name          = "${var.project_id}-embeddings"
  location      = var.region
  force_destroy = false
  project       = var.project_id
  
  uniform_bucket_level_access = true
  
  # Configure lifecycle rules for cost optimization
  lifecycle_rule {
    condition {
      age = 90  # Archive files older than 90 days
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  # Enable versioning for data protection
  versioning {
    enabled = true
  }
  
  # Enable CORS for web access if needed
  cors {
    origin = ["*"]
    method = ["GET", "HEAD", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  labels = merge(local.common_labels, {
    purpose = "vector-embeddings"
  })
}

# 3. GCS bucket for application data and uploads
resource "google_storage_bucket" "app_data_bucket" {
  name          = "${var.project_id}-app-data"
  location      = var.region
  force_destroy = false
  project       = var.project_id
  
  uniform_bucket_level_access = true
  
  # Configure lifecycle rules for cost optimization
  lifecycle_rule {
    condition {
      age = 365  # Archive files older than 1 year
    }
    action {
      type = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
  
  # Enable versioning for data protection
  versioning {
    enabled = true
  }
  
  labels = merge(local.common_labels, {
    purpose = "app-data"
  })
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

output "app_data_bucket" {
  value       = google_storage_bucket.app_data_bucket.name
  description = "Name of the GCS bucket for application data"
}
