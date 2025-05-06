# Agent Infrastructure Module for AI Orchestra
# This module creates the necessary GCP resources for the AI Orchestra agent system

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "redis.googleapis.com",
    "cloudtasks.googleapis.com",
    "pubsub.googleapis.com"
  ])
  
  project = var.project_id
  service = each.key
  
  disable_on_destroy = false
}

# Create service account for the application
resource "google_service_account" "orchestra_sa" {
  count        = var.service_account_create ? 1 : 0
  account_id   = var.service_account_name
  display_name = "Orchestra Service Account for ${var.environment}"
  project      = var.project_id
  
  depends_on = [google_project_service.required_apis]
}

# Grant necessary roles to the service account
resource "google_project_iam_member" "orchestra_sa_roles" {
  for_each = var.service_account_create ? toset(var.service_account_roles) : toset([])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestra_sa[0].email}"
  
  depends_on = [google_service_account.orchestra_sa]
}

# Create Secret Manager secrets
resource "google_secret_manager_secret" "api_keys" {
  for_each = var.create_secrets ? var.secrets : {}
  
  secret_id = each.key
  project   = var.project_id
  
  replication {
    automatic = true
  }
  
  labels = {
    environment = var.environment
    service     = var.service_name
  }
  
  depends_on = [google_project_service.required_apis]
}

# Grant access to secrets for the service account
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each = var.create_secrets ? var.secrets : {}
  
  project   = var.project_id
  secret_id = google_secret_manager_secret.api_keys[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_create ? google_service_account.orchestra_sa[0].email : var.service_account_name}"
  
  depends_on = [
    google_secret_manager_secret.api_keys,
    google_service_account.orchestra_sa
  ]
}

# Create Firestore database
resource "google_firestore_database" "orchestra_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.required_apis]
}

# Create Redis instance for short-term memory
resource "google_redis_instance" "orchestra_cache" {
  name           = "${var.service_name}-cache-${var.environment}"
  project        = var.project_id
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region
  tier           = "BASIC"
  
  redis_version  = "REDIS_6_X"
  display_name   = "Orchestra Memory Cache (${var.environment})"
  
  labels = {
    environment = var.environment
    service     = var.service_name
  }
  
  depends_on = [google_project_service.required_apis]
}

# Create Cloud Storage bucket for artifacts
resource "google_storage_bucket" "orchestra_artifacts" {
  name          = "${var.project_id}-${var.service_name}-artifacts-${var.environment}"
  project       = var.project_id
  location      = var.region
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
  
  labels = {
    environment = var.environment
    service     = var.service_name
  }
  
  depends_on = [google_project_service.required_apis]
}

# Create Cloud Run service
resource "google_cloud_run_v2_service" "orchestra_api" {
  name     = "${var.service_name}-api-${var.environment}"
  project  = var.project_id
  location = var.region
  
  template {
    containers {
      image = var.container_image != null ? var.container_image : "gcr.io/${var.project_id}/${var.service_name}:${var.environment}"
      
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }
      
      # Environment variables
      dynamic "env" {
        for_each = merge(
          {
            "ENVIRONMENT"      = var.environment
            "GCP_PROJECT_ID"   = var.project_id
            "REDIS_HOST"       = google_redis_instance.orchestra_cache.host
            "REDIS_PORT"       = google_redis_instance.orchestra_cache.port
            "REDIS_TTL"        = tostring(var.memory_ttl)
            "FIRESTORE_DATABASE" = google_firestore_database.orchestra_db.name
          },
          var.env_vars
        )
        
        content {
          name  = env.key
          value = env.value
        }
      }
      
      # Secret environment variables
      dynamic "env" {
        for_each = var.secret_env_vars
        
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = env.value.version_id
            }
          }
        }
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    service_account = var.service_account_create ? google_service_account.orchestra_sa[0].email : var.service_account_name
    
    # VPC connector if provided
    dynamic "vpc_access" {
      for_each = var.vpc_connector != null ? [1] : []
      content {
        connector = var.vpc_connector
        egress    = var.vpc_egress
      }
    }
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_redis_instance.orchestra_cache,
    google_firestore_database.orchestra_db
  ]
}

# Allow unauthenticated access to the Cloud Run service if enabled
resource "google_cloud_run_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.region
  service  = google_cloud_run_v2_service.orchestra_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}