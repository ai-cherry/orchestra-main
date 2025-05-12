# Enhanced Performance Cloud Run Configuration for AI Orchestra
# Implements recommended resource configurations and optimized annotations

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "ai-orchestra"
}

variable "cloudsql_instance" {
  description = "CloudSQL instance connection name"
  type        = string
  default     = ""
}

variable "vpc_connector_name" {
  description = "VPC connector name"
  type        = string
  default     = ""
}

variable "image" {
  description = "Container image to deploy"
  type        = string
}

# Create Cloud Run service with performance optimizations
resource "google_cloud_run_service" "optimized_service" {
  name     = "${var.service_name}-${var.env}"
  location = var.region

  template {
    spec {
      containers {
        image = var.image
        
        # Enhanced resource configuration for optimized performance
        resources {
          limits = {
            cpu    = "2"
            memory = "1Gi"
          }
          requests = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
        
        # Health check for enhanced stability
        liveness_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 10
          period_seconds        = 15
          timeout_seconds       = 5
          failure_threshold     = 3
        }
      }
      
      # Optimize for stateful requests
      container_concurrency = 80
      timeout_seconds       = 300
    }
    
    metadata {
      annotations = {
        # Performance-optimized annotations
        "run.googleapis.com/cpu-throttling"          = "false"  # Eliminate cold start delays
        "run.googleapis.com/session-affinity"        = "true"   # Improve stateful workloads
        "run.googleapis.com/cloudsql-instances"      = var.cloudsql_instance != "" ? var.cloudsql_instance : null
        "run.googleapis.com/vpc-access-connector"    = var.vpc_connector_name != "" ? var.vpc_connector_name : null
        "run.googleapis.com/client-name"             = "ai-orchestra"
        "run.googleapis.com/client-protocol"         = "http1"
        "run.googleapis.com/execution-environment"   = "gen2"
        "run.googleapis.com/container-dependencies"  = "dependencies.yaml"
        "run.googleapis.com/startup-cpu-boost"       = "true"  # Accelerate initialization
        "autoscaling.knative.dev/minScale"           = "1"
        "autoscaling.knative.dev/maxScale"           = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# Allow public access
data "google_iam_policy" "public_access" {
  binding {
    role    = "roles/run.invoker"
    members = ["allUsers"]
  }
}

resource "google_cloud_run_service_iam_policy" "public_access" {
  location    = google_cloud_run_service.optimized_service.location
  project     = google_cloud_run_service.optimized_service.project
  service     = google_cloud_run_service.optimized_service.name
  policy_data = data.google_iam_policy.public_access.policy_data
}

# Create Cloud Scheduler job to prevent cold starts
resource "google_cloud_scheduler_job" "keep_warm" {
  name        = "${var.service_name}-${var.env}-keep-warm"
  description = "Periodically warm the service to prevent cold starts"
  schedule    = "*/5 * * * *"  # Every 5 minutes
  
  http_target {
    uri         = google_cloud_run_service.optimized_service.status[0].url
    http_method = "GET"
    
    headers = {
      "User-Agent" = "Google-Cloud-Scheduler"
    }
  }
}

output "service_url" {
  value = google_cloud_run_service.optimized_service.status[0].url
}