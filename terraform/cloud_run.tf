# Cloud Run deployment for AI Orchestra

# Service account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "orchestra-cloud-run-sa"
  display_name = "AI Orchestra Cloud Run Service Account"
  description  = "Service account for AI Orchestra Cloud Run services"
  project      = var.project_id
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "cloud_run_sa_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/firestore.viewer"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Deploy the AI Orchestra API to Cloud Run
module "ai_orchestra_api" {
  source = "./modules/cloud-run"

  project_id            = var.project_id
  region                = var.region
  env                   = var.env
  service_name          = "ai-orchestra-api"
  container_image       = "gcr.io/${var.project_id}/ai-orchestra-api:latest"
  service_account_email = google_service_account.cloud_run_sa.email

  # Resource allocation
  cpu    = "1000m"
  memory = "2Gi"

  # Scaling configuration
  min_instances = 1
  max_instances = 10

  # Container configuration
  container_port        = 8000
  container_concurrency = 80
  timeout_seconds       = 300

  # Environment variables
  environment_variables = {
    PROJECT_ID = var.project_id
    ENV        = var.env
    REGION     = var.region
    LOG_LEVEL  = "INFO"
  }

  # Secret environment variables
  secret_environment_variables = {
    VERTEX_API_KEY = {
      secret_name = "vertex-power-key"
      secret_key  = "latest"
    },
    GEMINI_API_KEY = {
      secret_name = "gemini-power-key"
      secret_key  = "latest"
    }
  }

  # Access control
  public_access = true
  invoker_members = [
    "serviceAccount:${google_service_account.cloud_run_sa.email}"
  ]

  # Domain mapping (optional)
  domain_name = var.domain_names["api"]

  # Secrets (optional)
  secrets = {
    "api-key" = var.api_keys["main"]
  }

  # Monitoring (optional)
  enable_monitoring    = true
  error_rate_threshold = 0.05
  notification_channels = [
    var.notification_channels[0]
  ]

  # Scheduler (optional)
  scheduler_config = {
    schedule              = "*/10 * * * *"  # Every 10 minutes
    http_method           = "GET"
    service_account_email = google_service_account.cloud_run_sa.email
  }
}

# Deploy the AI Orchestra UI to Cloud Run
module "ai_orchestra_ui" {
  source = "./modules/cloud-run"

  project_id            = var.project_id
  region                = var.region
  env                   = var.env
  service_name          = "ai-orchestra-ui"
  container_image       = "gcr.io/${var.project_id}/ai-orchestra-ui:latest"
  service_account_email = google_service_account.cloud_run_sa.email

  # Resource allocation
  cpu    = "1000m"
  memory = "1Gi"

  # Scaling configuration
  min_instances = 1
  max_instances = 5

  # Container configuration
  container_port        = 3000
  container_concurrency = 80
  timeout_seconds       = 60

  # Environment variables
  environment_variables = {
    PROJECT_ID = var.project_id
    ENV        = var.env
    API_URL    = module.ai_orchestra_api.service_url
  }

  # Access control
  public_access = true

  # Domain mapping (optional)
  domain_name = var.domain_names["ui"]

  # Monitoring (optional)
  enable_monitoring    = true
  error_rate_threshold = 0.05
  notification_channels = [
    var.notification_channels[0]
  ]
}

# Outputs
output "api_url" {
  description = "The URL of the AI Orchestra API"
  value       = module.ai_orchestra_api.service_url
}

output "ui_url" {
  description = "The URL of the AI Orchestra UI"
  value       = module.ai_orchestra_ui.service_url
}

output "api_domain_mapping_status" {
  description = "The status of the API domain mapping"
  value       = module.ai_orchestra_api.domain_mapping_status
}

output "ui_domain_mapping_status" {
  description = "The status of the UI domain mapping"
  value       = module.ai_orchestra_ui.domain_mapping_status
}