terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.0.0"
}

provider "google" {
  # Configuration options
  # The credentials will be sourced from the environment when deployed
  # project = "your-gcp-project-id"  # Uncomment and set your project ID
  # region  = "us-central1"          # Uncomment and set your preferred region
}

# Example resource - a Cloud Storage bucket
resource "google_storage_bucket" "example_bucket" {
  name          = "orchestra-example-bucket"  # Replace with a globally unique bucket name
  location      = "US"
  force_destroy = true
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Output the bucket URL
output "bucket_url" {
  value = google_storage_bucket.example_bucket.url
}