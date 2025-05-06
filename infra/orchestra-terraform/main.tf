/**
* Orchestra Infrastructure Terraform Configuration
 *
 * This configuration provisions:
 * - Redis instance with 3GB capacity
 * - Secret Manager with Redis authentication
 * - Enables required APIs
 */

# Configure the GCS backend for Terraform state with state locking
terraform {
  required_version = "~> 1.11.3" # Specify exact Terraform version
  
  backend "gcs" {
    # Configuration is provided during terraform init via -backend-config
    # State locking enabled with storage.objects.update permission
    encryption_key = null # Use Google-managed encryption
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0" # Keeping compatible with existing version
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0" # Keeping compatible with existing version
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0" # Compatible with existing version
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0" # Compatible with existing version
    }
  }
}

# Implement modern provider configuration with alias support
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
    "sqladmin.googleapis.com", # For Cloud SQL operations
    "vpcaccess.googleapis.com", # For VPC Access Connector
    "iam.googleapis.com",      # For Workload Identity Federation
    "iamcredentials.googleapis.com" # For Workload Identity token creation
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

# Redis Instance with modern GCP provider syntax
resource "google_redis_instance" "cache" {
  name           = "orchestra-redis"
  tier           = "BASIC"
  memory_size_gb = 3

  region      = var.region
  location_id = var.zone
  
  # Modern features
  read_replicas_mode = "READ_REPLICAS_DISABLED"
  connect_mode       = "DIRECT_PEERING"
  
  redis_version     = "REDIS_6_X"
  display_name      = "Orchestra Cache"
  reserved_ip_range = "10.0.0.0/29"

  maintenance_policy {
    weekly_maintenance_window {
      day = "SATURDAY"
      start_time {
        hours   = 2
        minutes = 0
      }
    }
  }

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

# Workload Identity Federation for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool-${var.env}"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
  disabled                  = false
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider-${var.env}"
  display_name                       = "GitHub Actions Provider"
  description                        = "OIDC identity pool provider for GitHub Actions"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Service account for GitHub Actions to assume
resource "google_service_account" "github_actions" {
  account_id   = "github-actions-${var.env}"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions to deploy Terraform"
}

# Allow GitHub Actions to impersonate the service account
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/<YOUR_GITHUB_ORG>/orchestra-main"
  ]
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "terraform_deployer_permissions" {
  for_each = toset([
    "roles/editor",  # Broad role, consider limiting in production
    "roles/storage.admin"  # For state bucket access
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# IAM - Grant the Cloud Run service account permission to use the VPC connector
resource "google_project_iam_member" "cloud_run_vpc_connector_user" {
  project = var.project_id
  role    = "roles/vpcaccess.connectorUser"
  member  = "serviceAccount:${google_service_account.cloud_run_identity.email}"
}

# Output connection details as JSON
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

# Output Workload Identity Pool Provider information
output "workload_identity_provider" {
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  description = "The Workload Identity Provider for GitHub Actions"
}

output "service_account_email" {
  value       = google_service_account.github_actions.email
  description = "The Service Account email for GitHub Actions to impersonate"
}
