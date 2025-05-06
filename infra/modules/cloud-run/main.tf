variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

variable "image" {
  description = "Container image URL"
  type        = string
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 20
}

variable "cpu_always_allocated" {
  description = "Whether CPU is always allocated"
  type        = bool
  default     = true
}

variable "firestore_namespace" {
  description = "Firestore namespace"
  type        = string
}

variable "vector_index_name" {
  description = "Vector index name"
  type        = string
}

# Service account for Cloud Run
resource "google_service_account" "orchestrator_sa" {
  account_id   = "orchestrator-${var.env}-sa"
  display_name = "Orchestrator ${var.env} Service Account"
  description  = "Service account for the Orchestra ${var.env} API"
}

# Grant IAM roles to the service account - least privilege principle
resource "google_project_iam_member" "firestore_access" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "redis_user" {
  project = var.project_id
  role    = "roles/redis.editor"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "logs_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# Cloud Run service
resource "google_cloud_run_service" "orchestrator" {
  name     = "orchestrator-api-${var.env}"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"        = var.min_instances
        "autoscaling.knative.dev/maxScale"        = var.max_instances
        "run.googleapis.com/cpu-throttling"       = var.cpu_always_allocated ? "false" : "true"
        # Connect to VPC
        "run.googleapis.com/vpc-access-connector" = "projects/${var.project_id}/locations/${var.region}/connectors/orchestrator-vpc-connector-${var.env}"
        "run.googleapis.com/vpc-access-egress"    = "private-ranges-only"
        # Adding health check configurations as annotations instead of blocks
        "run.googleapis.com/startup-probe-path"   = "/api/health"
        "run.googleapis.com/startup-probe-period-seconds" = "5"
        "run.googleapis.com/liveness-probe-path"  = "/api/health" 
        "run.googleapis.com/liveness-probe-period-seconds" = "30"
      }
      labels = {
        "environment" = var.env
      }
    }

    spec {
      service_account_name = google_service_account.orchestrator_sa.email

      containers {
        image = var.image

        # Required environment variables
        env {
          name  = "ENVIRONMENT"
          value = var.env
        }

        env {
          name  = "FIRESTORE_NAMESPACE"
          value = var.firestore_namespace
        }

        env {
          name  = "VECTOR_INDEX_NAME"
          value = var.vector_index_name
        }

        # Secret references
        env {
          name  = "OPENROUTER_API_KEY"
          value_from {
            secret_key_ref {
              name = "openrouter-${var.env}"
              key  = "latest"
            }
          }
        }
        
        env {
          name  = "PORTKEY_API_KEY"
          value_from {
            secret_key_ref {
              name = "portkey-api-key-${var.env}"
              key  = "latest"
            }
          }
        }

        # Configuration
        env {
          name  = "LOG_LEVEL"
          value = var.env == "prod" ? "INFO" : "DEBUG"
        }

        env {
          name  = "PUBSUB_TOPIC"
          value = "orchestra-bus-${var.env}"
        }

        # Redis configuration
        env {
          name  = "REDIS_HOST"
          value = "orchestrator-cache-${var.env}.redis.cache.windows.net"  # This will be replaced with actual Redis host
        }
        
        env {
          name  = "REDIS_PORT"
          value = "6379"
        }
        
        env {
          name  = "REDIS_AUTH_SECRET"
          value = "redis-auth-${var.env}"
        }

        # Container resources
        resources {
          limits = {
            cpu    = var.env == "prod" ? "2000m" : "1000m"
            memory = var.env == "prod" ? "4Gi" : "2Gi"
          }
        }
      }
      
      # Container concurrency (how many concurrent requests)
      container_concurrency = 80
      
      # Set reasonable timeouts
      timeout_seconds = 300
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  # Add canary revision for testing (10% traffic)
  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
      metadata[0].annotations["run.googleapis.com/operation-id"],
    ]
  }
}

# Create a canary revision with larger instances (optional, commented out by default)
/*
resource "google_cloud_run_service" "orchestrator_canary" {
  count    = var.env == "prod" ? 1 : 0
  name     = "orchestrator-api-${var.env}-canary"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"        = var.min_instances
        "autoscaling.knative.dev/maxScale"        = var.max_instances
        "run.googleapis.com/cpu-throttling"       = "false"
      }
      labels = {
        "environment" = var.env
        "traffic"     = "canary"
      }
    }

    spec {
      service_account_name = google_service_account.orchestrator_sa.email

      containers {
        image = var.image

        env {
          name  = "ENVIRONMENT"
          value = var.env
        }

        env {
          name  = "FIRESTORE_NAMESPACE"
          value = var.firestore_namespace
        }

        env {
          name  = "VECTOR_INDEX_NAME"
          value = var.vector_index_name
        }

        env {
          name  = "OPENROUTER_KEY"
          value = "projects/${var.project_id}/secrets/openrouter/versions/latest"
        }

        env {
          name  = "LOG_LEVEL"
          value = "DEBUG"
        }

        env {
          name  = "PUBSUB_TOPIC"
          value = "orchestra-bus-${var.env}"
        }

        resources {
          limits = {
            cpu    = "2000m"  # Larger CPU allocation for canary
            memory = "4Gi"    # More memory for canary
          }
        }
      }
    }
  }

  traffic {
    percent         = 10
    latest_revision = true
  }
}
*/

# Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_service.orchestrator.location
  project  = var.project_id
  service  = google_cloud_run_service.orchestrator.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "url" {
  value = google_cloud_run_service.orchestrator.status[0].url
}

output "service_account" {
  value = google_service_account.orchestrator_sa.email
}
