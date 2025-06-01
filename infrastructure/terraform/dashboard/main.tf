# Terraform configuration for Admin UI infrastructure
# Deploys to Google Cloud Platform with auto-scaling and monitoring

terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    prefix = "terraform/admin-ui"
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be production, staging, or development."
  }
}

# Local variables
locals {
  service_name = "admin-ui-${var.environment}"
  labels = {
    app         = "admin-ui"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "containerregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com"
  ])
  
  service            = each.value
  disable_on_destroy = false
}

# Service Account for Cloud Run
resource "google_service_account" "admin_ui" {
  account_id   = "${local.service_name}-sa"
  display_name = "Admin UI Service Account"
  description  = "Service account for Admin UI Cloud Run service"
}

# IAM roles for service account
resource "google_project_iam_member" "admin_ui_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/secretmanager.secretAccessor"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.admin_ui.email}"
}

# Secret Manager for API keys
resource "google_secret_manager_secret" "api_key" {
  secret_id = "${local.service_name}-api-key"
  
  replication {
    auto {}
  }
  
  labels = local.labels
}

resource "google_secret_manager_secret_version" "api_key" {
  secret      = google_secret_manager_secret.api_key.id
  secret_data = "placeholder-api-key" # This should be set via CI/CD
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "admin_ui" {
  name     = local.service_name
  location = var.region
  
  template {
    service_account = google_service_account.admin_ui.email
    
    scaling {
      min_instance_count = var.environment == "production" ? 2 : 1
      max_instance_count = var.environment == "production" ? 100 : 10
    }
    
    containers {
      image = "gcr.io/${var.project_id}/admin-ui:${var.environment}-latest"
      
      resources {
        limits = {
          cpu    = var.environment == "production" ? "2" : "1"
          memory = var.environment == "production" ? "1Gi" : "512Mi"
        }
        cpu_idle = true
      }
      
      env {
        name  = "NODE_ENV"
        value = "production"
      }
      
      env {
        name = "API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.api_key.secret_id
            version = "latest"
          }
        }
      }
      
      ports {
        container_port = 3000
      }
      
      startup_probe {
        initial_delay_seconds = 0
        timeout_seconds       = 1
        period_seconds        = 3
        failure_threshold     = 1
        tcp_socket {
          port = 3000
        }
      }
      
      liveness_probe {
        http_get {
          path = "/api/health"
        }
        initial_delay_seconds = 10
        period_seconds        = 10
        timeout_seconds       = 5
        failure_threshold     = 3
      }
    }
    
    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.id
        subnetwork = google_compute_subnetwork.subnet.id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  labels = local.labels
  
  depends_on = [google_project_service.required_apis]
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${local.service_name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${local.service_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  
  private_ip_google_access = true
}

# Cloud Armor Security Policy
resource "google_compute_security_policy" "admin_ui" {
  name = "${local.service_name}-security-policy"
  
  # Rate limiting rule
  rule {
    action   = "throttle"
    priority = "1000"
    
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
    }
  }
  
  # Default rule
  rule {
    action   = "allow"
    priority = "2147483647"
    
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}

# Load Balancer with CDN
resource "google_compute_global_address" "admin_ui" {
  name = "${local.service_name}-ip"
}

resource "google_compute_managed_ssl_certificate" "admin_ui" {
  name = "${local.service_name}-cert"
  
  managed {
    domains = var.environment == "production" ? 
      ["admin.yourdomain.com"] : 
      ["admin-${var.environment}.yourdomain.com"]
  }
}

resource "google_compute_backend_service" "admin_ui" {
  name = "${local.service_name}-backend"
  
  backend {
    group = google_compute_region_network_endpoint_group.admin_ui_neg.id
  }
  
  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    default_ttl                  = 3600
    client_ttl                   = 7200
    max_ttl                      = 86400
    negative_caching             = true
    serve_while_stale            = 86400
    signed_url_cache_max_age_sec = 7200
  }
  
  security_policy = google_compute_security_policy.admin_ui.id
  
  health_checks = [google_compute_health_check.admin_ui.id]
  
  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_region_network_endpoint_group" "admin_ui_neg" {
  name                  = "${local.service_name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  
  cloud_run {
    service = google_cloud_run_v2_service.admin_ui.name
  }
}

resource "google_compute_health_check" "admin_ui" {
  name = "${local.service_name}-health-check"
  
  http_health_check {
    port         = 443
    request_path = "/api/health"
  }
  
  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3
}

# Monitoring Dashboard
resource "google_monitoring_dashboard" "admin_ui" {
  dashboard_json = jsonencode({
    displayName = "Admin UI Dashboard - ${var.environment}"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Request Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.label.\"service_name\"=\"${local.service_name}\""
                  }
                }
              }]
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Response Latency"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\" resource.label.\"service_name\"=\"${local.service_name}\""
                  }
                }
              }]
            }
          }
        }
      ]
    }
  })
}

# Alerting Policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "${local.service_name} - High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate > 5%"
    
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.label.\"service_name\"=\"${local.service_name}\" metric.label.\"response_code_class\"=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.environment == "production" ? 
    [google_monitoring_notification_channel.email.name] : []
  
  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Admin UI Alerts"
  type         = "email"
  
  labels = {
    email_address = "alerts@yourdomain.com"
  }
}

# Outputs
output "service_url" {
  value       = google_cloud_run_v2_service.admin_ui.uri
  description = "URL of the deployed Admin UI service"
}

output "load_balancer_ip" {
  value       = google_compute_global_address.admin_ui.address
  description = "IP address of the load balancer"
}