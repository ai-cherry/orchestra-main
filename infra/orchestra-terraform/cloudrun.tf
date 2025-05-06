/**
* Orchestra Cloud Run Services Terraform Configuration
 *
 * This configuration provisions:
 * - Orchestra API service with PostgreSQL and Redis connectivity
 * - Phidata Agent UI service with proper configuration
 */

# Orchestra API Service
resource "google_cloud_run_v2_service" "orchestra_api" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "orchestra-api-${var.env}"
  location = var.region

  template {
    containers {
      # Use a known placeholder image initially for Terraform apply
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      ports {
        container_port = 8080
      }

      env {
        name  = "ENVIRONMENT"
        value = var.env
      }

      # Redis environment variables
      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.cache.host
      }

      env {
        name  = "REDIS_PORT"
        value = google_redis_instance.cache.port
      }

      # Reference Redis password from Secret Manager
      env {
        name = "REDIS_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.redis_auth.id
            version = "latest"
          }
        }
      }

      # PostgreSQL environment variables
      env {
        name  = "POSTGRES_HOST"
        value = "/cloudsql/${google_sql_database_instance.phidata_postgres.connection_name}"
      }

      env {
        name  = "POSTGRES_DB"
        value = google_sql_database.phidata_memory.name
      }

      env {
        name  = "POSTGRES_USER"
        value = google_sql_user.phidata_user.name
      }

      env {
        name = "POSTGRES_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.postgres_password.id
            version = "latest"
          }
        }
      }

      # Add Cloud SQL connection volume mount
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    # VPC access configuration
    vpc_access {
      connector = google_vpc_access_connector.orchestra_connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    # Add Cloud SQL proxy sidecar volume
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.phidata_postgres.connection_name]
      }
    }

    # Use the dedicated service account with proper permissions
    service_account = google_service_account.cloud_run_identity.email
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.required_apis,
    google_redis_instance.cache,
    google_secret_manager_secret.redis_auth,
    google_sql_database_instance.phidata_postgres,
    google_sql_database.phidata_memory,
    google_secret_manager_secret.postgres_password
  ]
}

# Phidata Agent UI Service
resource "google_cloud_run_v2_service" "phidata_agent_ui" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "phidata-agent-ui-${var.env}"
  location = var.region

  template {
    containers {
      # Using a specific version tag for stability and reproducibility
      # Updated from 'latest' to ensure consistent deployments
      image = var.phidata_agent_ui_image

      ports {
        # Phidata Agent UI container listens on port 8000
        container_port = 8000
      }

      env {
        name  = "ENVIRONMENT"
        value = var.env
      }

      # Connect to Orchestra API
      env {
        # PHIDATA_API_URL is the environment variable Phidata Agent UI
        # uses to connect to the backend API
        name  = "PHIDATA_API_URL"
        value = var.create_cloud_run_services ? google_cloud_run_v2_service.orchestra_api[0].uri : ""
      }

      # Additional Phidata configuration variables
      env {
        name  = "PHIDATA_APP_NAME"
        value = "Orchestra"
      }

      env {
        name  = "PHIDATA_APP_DESCRIPTION"
        value = "Orchestra AI Agent Platform"
      }

      env {
        name  = "PHIDATA_TELEMETRY"
        value = "false"
      }

      # If using authentication
      env {
        name  = "PHIDATA_AUTH_ENABLED"
        value = "true"
      }

      # Enable debug mode for development environment
      env {
        name  = "PHIDATA_DEBUG"
        value = var.env == "dev" ? "true" : "false"
      }
    }

    # Use the project's default service account
    # No need for Cloud SQL access for the UI container
    service_account = "${var.project_id}@appspot.gserviceaccount.com"
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.required_apis
  ]
}

# IAM - Allow public access to the Phidata Agent UI
resource "google_cloud_run_service_iam_member" "phidata_agent_ui_public" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.phidata_agent_ui[0].location
  service  = google_cloud_run_v2_service.phidata_agent_ui[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# IAM - Grant the Cloud Run service account access to the Redis auth secret
resource "google_secret_manager_secret_iam_member" "redis_secret_access" {
  secret_id = google_secret_manager_secret.redis_auth.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_identity.email}"
}

# Output Cloud Run service URLs
output "service_urls" {
  value = var.create_cloud_run_services ? {
    api = google_cloud_run_v2_service.orchestra_api[0].uri
    ui  = google_cloud_run_v2_service.phidata_agent_ui[0].uri
  } : {}
}
