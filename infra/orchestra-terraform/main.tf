/**
* Orchestra Infrastructure Terraform Configuration
 *
 * This configuration provisions:
 * - Redis instance with 3GB capacity
 * - Secret Manager with Redis authentication
 * - Enables required APIs
 */

# Configure the GCS backend for Terraform state
terraform {
  backend "gcs" {
    # Configuration is provided during terraform init via -backend-config
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0" # Specify a version constraint
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0" # Specify a version constraint
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0" # Specify a version constraint
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0" # Specify a version constraint
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.region
  zone        = "${var.region}-a"
}

provider "google-beta" {
  project     = var.project_id
  region      = var.region
  zone        = "${var.region}-a"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "aiplatform.googleapis.com",
    "firestore.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "sqladmin.googleapis.com",  # For Cloud SQL operations
    "vpcaccess.googleapis.com"  # For VPC Access Connector
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Redis Instance - Removed alternative_location_id which was causing issues
resource "google_redis_instance" "cache" {
  name           = "orchestra-redis"
  tier           = "BASIC"
  memory_size_gb = 3

  region                  = var.region
  location_id             = var.zone
  # Removed alternative_location_id as it's not supported for BASIC tier

  redis_version     = "REDIS_6_X"
  display_name      = "Orchestra Cache"
  reserved_ip_range = "10.0.0.0/29"

  depends_on = [google_project_service.required_apis]
  
  lifecycle {
    ignore_changes = [
      memory_size_gb,
      display_name,
      redis_version
    ]
  }
}

# Secret Manager - Redis Password
resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "redis-auth-${var.env}"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "redis_auth_value" {
  secret      = google_secret_manager_secret.redis_auth.id
  secret_data = random_password.redis_password.result
}

# Generate Random Redis Password
resource "random_password" "redis_password" {
  length  = 16
  special = true
}

# Output connection details as JSON
output "connection_details" {
  value = jsonencode({
    redis = {
      host     = google_redis_instance.cache.host
      port     = google_redis_instance.cache.port
      password_secret = google_secret_manager_secret.redis_auth.name
    }
  })
  sensitive = true
}

# IAM - Grant the Cloud Run service account permission to use the VPC connector
resource "google_project_iam_member" "cloud_run_vpc_connector_user" {
  project = var.project_id
  role    = "roles/vpcaccess.connectorUser"
  member  = "serviceAccount:${google_service_account.cloud_run_identity.email}"
}
