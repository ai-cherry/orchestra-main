/**
 * Main configuration for cherry-ai-project common resources
 */

terraform {
  required_version = ">= 1.0"
  
  backend "gcs" {
    bucket  = "tfstate-cherry-ai-project"
    prefix  = "terraform/state/common"
  }
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

# Provider configurations are in iam.tf to avoid circular dependencies
