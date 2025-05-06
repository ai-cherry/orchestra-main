/**
 * Storage resources for orchestra project
 */

# GCS bucket for Terraform state storage
resource "google_storage_bucket" "terraform_state" {
  name          = "tfstate-cherry-ai-me-orchestra"
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
  
  retention_policy {
    is_locked = false
    retention_period = 2592000  # 30 days in seconds
  }
  
  labels = merge(local.common_labels, {
    purpose = "terraform-state"
    project = "cherry-ai-me-orchestra"
  })
}

# GCS bucket for embeddings storage
resource "google_storage_bucket" "embeddings_bucket" {
  name          = "cherry-ai-me-embeddings"
  location      = var.region
  force_destroy = false
  project       = var.project_id
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 90  # Archive files older than 90 days
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  versioning {
    enabled = true
  }
  
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

# GCS bucket for application data and uploads
resource "google_storage_bucket" "app_data_bucket" {
  name          = "cherry-ai-me-app-data"
  location      = var.region
  force_destroy = false
  project       = var.project_id
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 365  # Archive files older than 1 year
    }
    action {
      type = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
  
  versioning {
    enabled = true
  }
  
  labels = merge(local.common_labels, {
    purpose = "app-data"
  })
}
