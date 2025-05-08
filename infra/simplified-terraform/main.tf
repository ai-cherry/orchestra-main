/**
 * Orchestra Infrastructure Simplified Terraform Configuration
 *
 * This configuration provisions:
 * - Single service account with broad permissions for development
 * - Redis instance with 5GB capacity for better performance
 * - Secret Manager with Redis authentication
 * - Enables required APIs
 */

terraform {
  required_version = "~> 1.11.3"
  
  # Use local state for faster development
  # backend "gcs" can be added later when needed
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = "${var.region}-a"
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = "${var.region}-a"
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
    "sqladmin.googleapis.com",
    "vpcaccess.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com"
  ])

  project = var.project_id
  service = each.key
  
  disable_dependent_services = false
  disable_on_destroy         = false
  
  # Prevent service API disable failures
  timeouts {
    create = "30m"
    update = "40m"
  }
}

# Single service account for all operations
resource "google_service_account" "orchestra_service_account" {
  account_id   = "orchestra-service-account-${var.env}"
  display_name = "Orchestra Service Account"
  description  = "Single service account for all Orchestra operations"
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "service_account_permissions" {
  for_each = toset([
    "roles/editor",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor",
    "roles/cloudsql.client",
    "roles/redis.editor",
    "roles/run.admin",
    "roles/storage.admin"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestra_service_account.email}"
}

# Redis Instance optimized for performance
resource "google_redis_instance" "cache" {
  name           = "orchestra-redis-${var.env}"
  tier           = "BASIC"
  memory_size_gb = var.redis_memory_size_gb
  
  region      = var.region
  location_id = var.zone
  
  redis_version     = var.redis_version
  display_name      = "Orchestra Cache"
  reserved_ip_range = "10.0.0.0/29"
  
  # Simplified maintenance policy
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }
  
  depends_on = [google_project_service.required_apis]
  
  lifecycle {
    prevent_destroy = false  # Allow destruction for development
  }
}

# Generate Random Redis Password
resource "random_password" "redis_password" {
  length  = 16
  special = true
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

# Output connection details
output "connection_details" {
  value = jsonencode({
    redis = {
      host            = google_redis_instance.cache.host
      port            = google_redis_instance.cache.port
      password_secret = google_secret_manager_secret.redis_auth.name
    }
  })
  sensitive = true
}

output "redis_host" {
  value     = google_redis_instance.cache.host
  sensitive = false
}

output "redis_port" {
  value     = google_redis_instance.cache.port
  sensitive = false
}

output "service_account_email" {
  value       = google_service_account.orchestra_service_account.email
  description = "The Service Account email for Orchestra services"
  sensitive   = false
}