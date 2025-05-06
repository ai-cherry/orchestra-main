terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
  
  backend "gcs" {
    bucket  = "tfstate-cherry-ai-project"
    prefix  = "terraform/state/prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

locals {
  env      = var.env
  location = var.region
  labels = {
    environment = local.env
    managed-by  = "terraform"
    project     = "orchestra"
  }
}

# Cloud Storage bucket for production data
resource "google_storage_bucket" "orchestrator_storage" {
  name          = "orchestrator-${local.env}-storage-${var.project_id}"
  location      = var.region
  storage_class = "STANDARD"
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 60
    }
    action {
      type = "Delete"
    }
  }
  
  labels = local.labels
  
  uniform_bucket_level_access = true
}
