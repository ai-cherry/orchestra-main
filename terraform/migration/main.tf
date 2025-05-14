# main.tf 
# Main Terraform configuration for AI Orchestra GCP Migration

# Enable required GCP APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "containerregistry.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com", 
    "alloydb.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "iamcredentials.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# Service account for Cloud Run
resource "google_service_account" "service_account" {
  account_id   = var.service_account_id
  display_name = "AI Orchestra Service Account"
  project      = var.project_id
  
  depends_on = [google_project_service.required_apis]
}

# Grant necessary IAM roles to the service account
resource "google_project_iam_member" "service_account_roles" {
  for_each = toset([
    "roles/run.invoker",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor",
    "roles/firestore.user"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.service_account.email}"
}

# Secret for API keys and sensitive configuration
resource "google_secret_manager_secret" "api_key" {
  secret_id = "ai-orchestra-api-key"
  project   = var.project_id
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

# Initial version of the secret
resource "google_secret_manager_secret_version" "api_key_version" {
  secret      = google_secret_manager_secret.api_key.id
  secret_data = "initial-api-key-replace-in-production"
}

# Allow service account to access the secret
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id  = google_secret_manager_secret.api_key.id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.service_account.email}"
  project    = var.project_id
}

# Cloud Run service configuration
resource "google_cloud_run_service" "api_service" {
  name     = var.cloud_run_service_name
  location = var.region
  project  = var.project_id
  
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/${var.cloud_run_service_name}:latest"
        
        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }
        
        # Environment variables
        env {
          name  = "ENV"
          value = var.env
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        # Secret environment variable
        env {
          name = "API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.api_key.secret_id
              key  = "latest"
            }
          }
        }
      }
      
      container_concurrency = var.container_concurrency
      timeout_seconds       = var.timeout_seconds
      service_account_name  = google_service_account.service_account.email
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances
        "run.googleapis.com/vpc-access-connector" = var.vpc_connector_name
        "run.googleapis.com/vpc-access-egress" = "private-ranges-only"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_service_account.service_account,
    google_project_iam_member.service_account_roles
  ]
  
  autogenerate_revision_name = true
}

# Make service public (remove or modify for production as needed)
data "google_iam_policy" "public_access" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "public_access" {
  location    = google_cloud_run_service.api_service.location
  project     = google_cloud_run_service.api_service.project
  service     = google_cloud_run_service.api_service.name
  policy_data = data.google_iam_policy.public_access.policy_data
}

# Keep service warm with scheduled jobs
resource "google_cloud_scheduler_job" "keep_warm_job" {
  name      = "${var.cloud_run_service_name}-warmer"
  schedule  = "*/15 * * * *"  # Every 15 minutes
  project   = var.project_id
  region    = var.region
  time_zone = "Etc/UTC"

  http_target {
    uri         = google_cloud_run_service.api_service.status[0].url
    http_method = "GET"
    headers = {
      "User-Agent" = "Google-Cloud-Scheduler"
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Note: AlloyDB configuration has been removed temporarily due to compatibility issues.
# It will be implemented in a separate module after the base migration is completed.