# Google SDK Configuration for Terraform
# Enhances the Terraform development environment with Google Cloud SDK settings

# Configure additional SDK-specific options for the Google provider
provider "google" {
  # The following settings are merged with existing provider configuration
  
  # Configure request batching for more efficient API calls
  request_timeout = "60s"
  request_reason  = "terraform-orchestra-infrastructure"
  
  # Set default scopes for SDK operations
  scopes = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
  ]
}

# Configure additional SDK-specific options for the Google Beta provider
provider "google-beta" {
  # The following settings are merged with existing provider configuration
  
  # Configure request batching for more efficient API calls
  request_timeout = "60s"
  request_reason  = "terraform-orchestra-infrastructure"
  
  # Set default scopes for SDK operations
  scopes = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
  ]
}

# Configure local development settings
locals {
  # SDK-specific settings
  gcp_sdk_config = {
    # Default settings for authentication retry
    retry_configs = {
      default = {
        retry_conditions = ["unavailable", "deadline-exceeded"]
        max_retry_delay  = "60s"
        min_retry_delay  = "1s"
        max_retries      = 10
      }
    }
    
    # Default zones by region for Google SDK operations
    default_zones_by_region = {
      "us-central1" = "us-central1-a"
      "us-west1"    = "us-west1-b"
      "us-east1"    = "us-east1-b"
      "europe-west1" = "europe-west1-b"
      "asia-east1"   = "asia-east1-a"
    }
  }
}