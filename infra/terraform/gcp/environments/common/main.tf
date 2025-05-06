/**
 * Main configuration for the Orchestra project common environment
 * Defines provider requirements and global settings
 */

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
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

# Local variables for common configuration
locals {
  common_labels = {
    managed-by  = "terraform"
    environment = "common"
    project     = "ai-orchestra"
  }
  
  # Environment-specific prefixes for resource naming
  env_prefix = "orchestra"
}
