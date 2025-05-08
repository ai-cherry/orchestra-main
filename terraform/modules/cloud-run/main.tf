# Cloud Run Terraform Module for AI Orchestra

# Cloud Run service using v2 API
resource "google_cloud_run_v2_service" "service" {
  name     = "${var.service_name}-${var.env}"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = var.container_image

      # Set resource limits
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      # Set environment variables
      dynamic "env" {
        for_each = var.environment_variables
        content {
          name  = env.key
          value = env.value
        }
      }

      # Set secrets as environment variables
      dynamic "secrets" {
        for_each = var.secret_environment_variables
        content {
          name    = secrets.key
          secret  = secrets.value.secret_name
          version = "latest"
        }
      }

      # Set ports
      ports {
        container_port = var.container_port
      }
    }

    # Set service account
    service_account = var.service_account_email
    
    # Set container concurrency
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    max_instance_request_concurrency = var.container_concurrency
    
    # Set timeout
    timeout = "${var.timeout_seconds}s"
    
    # Set scaling with optimized settings
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }

  # Set traffic
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  # Ignore changes to image and other fields that are updated outside of Terraform
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}

# IAM policy for Cloud Run service
resource "google_cloud_run_v2_service_iam_policy" "noauth" {
  location    = google_cloud_run_v2_service.service.location
  project     = google_cloud_run_v2_service.service.project
  name        = google_cloud_run_v2_service.service.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

# IAM policy data for Cloud Run service
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = var.public_access ? [
      "allUsers",
    ] : var.invoker_members
  }
}

# Cloud Run domain mapping
resource "google_cloud_run_v2_domain_mapping" "domain_mapping" {
  count = var.domain_name != "" ? 1 : 0

  location = var.region
  project  = var.project_id
  name     = var.domain_name
  service  = google_cloud_run_v2_service.service.name
}

# Secret Manager secrets for Cloud Run
resource "google_secret_manager_secret" "secrets" {
  for_each = var.secrets

  project   = var.project_id
  secret_id = "${var.service_name}-${var.env}-${each.key}"

  replication {
    auto {}
  }
}

# Secret Manager secret versions
resource "google_secret_manager_secret_version" "secret_versions" {
  for_each = var.secrets

  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data = each.value
}

# IAM policy for Secret Manager
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each = var.secrets

  project   = var.project_id
  secret_id = google_secret_manager_secret.secrets[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

# Cloud Scheduler job for scheduled invocations (optional)
resource "google_cloud_scheduler_job" "scheduler_job" {
  count = var.scheduler_config != null ? 1 : 0

  name        = "${var.service_name}-${var.env}-scheduler"
  description = "Scheduler for ${var.service_name} Cloud Run service"
  schedule    = var.scheduler_config.schedule
  project     = var.project_id
  region      = var.region

  http_target {
    http_method = var.scheduler_config.http_method
    uri         = google_cloud_run_v2_service.service.uri
    
    oidc_token {
      service_account_email = var.scheduler_config.service_account_email
      audience              = google_cloud_run_v2_service.service.uri
    }
  }
}

# Cloud Monitoring alerting policy (optional)
resource "google_monitoring_alert_policy" "alert_policy" {
  count = var.enable_monitoring ? 1 : 0

  display_name = "${var.service_name}-${var.env}-error-rate"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Error rate for ${var.service_name}"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${google_cloud_run_v2_service.service.name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"4xx\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.error_rate_threshold
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }

      trigger {
        count = 1
      }
    }
  }

  notification_channels = var.notification_channels
}

# Outputs
output "service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.service.uri
}

output "service_name" {
  description = "The name of the Cloud Run service"
  value       = google_cloud_run_v2_service.service.name
}

output "domain_mapping_status" {
  description = "The status of the domain mapping"
  value       = var.domain_name != "" ? google_cloud_run_v2_domain_mapping.domain_mapping[0].status : null
}