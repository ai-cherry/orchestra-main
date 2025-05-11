# Terraform configuration for MCP Server infrastructure
# Optimized for performance and rapid deployment

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
  
  # Use a GCS bucket for remote state
  backend "gcs" {
    # These values should be provided via -backend-config options
    # bucket = "cherry-ai-project-terraform-state"
    # prefix = "mcp-server"
  }
}

# Variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "mcp-server"
}

variable "redis_instance_name" {
  description = "Name of the Redis instance"
  type        = string
  default     = "mcp-redis"
}

variable "vpc_connector_name" {
  description = "Name of the VPC connector"
  type        = string
  default     = "vpc-connector"
}

# Environment-specific configurations
locals {
  env_config = {
    dev = {
      min_instances     = 0
      max_instances     = 5
      cpu               = 1
      memory            = 512
      concurrency       = 20
      redis_tier        = "BASIC"
      redis_size_gb     = 1
      redis_version     = "REDIS_6_X"
    }
    staging = {
      min_instances     = 1
      max_instances     = 10
      cpu               = 1
      memory            = 1024
      concurrency       = 40
      redis_tier        = "STANDARD_HA"
      redis_size_gb     = 5
      redis_version     = "REDIS_6_X"
    }
    prod = {
      min_instances     = 2
      max_instances     = 100
      cpu               = 2
      memory            = 2048
      concurrency       = 80
      redis_tier        = "STANDARD_HA"
      redis_size_gb     = 10
      redis_version     = "REDIS_6_X"
    }
  }
  
  config = local.env_config[var.env]
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# VPC Network
resource "google_compute_network" "vpc_network" {
  name                    = "mcp-network-${var.env}"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "vpc_subnetwork" {
  name          = "mcp-subnetwork-${var.env}"
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.vpc_network.id
  region        = var.region
}

# VPC Connector
resource "google_vpc_access_connector" "connector" {
  name          = "${var.vpc_connector_name}-${var.env}"
  region        = var.region
  network       = google_compute_network.vpc_network.name
  ip_cidr_range = "10.8.0.0/28"
  
  # Performance optimization
  min_instances = 2
  max_instances = 10
  
  depends_on = [
    google_compute_network.vpc_network
  ]
}

# Redis instance
resource "google_redis_instance" "redis" {
  name               = "${var.redis_instance_name}-${var.env}"
  tier               = local.config.redis_tier
  memory_size_gb     = local.config.redis_size_gb
  region             = var.region
  redis_version      = local.config.redis_version
  authorized_network = google_compute_network.vpc_network.id
  
  # Performance optimizations
  redis_configs = {
    maxmemory-policy = "volatile-lru"
    notify-keyspace-events = "KEA"
    timeout = 3600
  }
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours = 2
        minutes = 0
      }
    }
  }
  
  depends_on = [
    google_compute_network.vpc_network
  ]
}

# Secret Manager - Redis credentials
resource "google_secret_manager_secret" "redis_credentials" {
  secret_id = "redis-credentials-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret_version" "redis_credentials_version" {
  secret = google_secret_manager_secret.redis_credentials.id
  
  secret_data = jsonencode({
    host = google_redis_instance.redis.host
    port = google_redis_instance.redis.port
  })
}

# Cloud Run service
resource "google_cloud_run_service" "mcp_server" {
  name     = "${var.service_name}-${var.env}"
  location = var.region
  
  template {
    spec {
      containers {
        # Image will be set by CI/CD pipeline
        image = "gcr.io/${var.project_id}/${var.service_name}:latest"
        
        resources {
          limits = {
            cpu    = "${local.config.cpu}"
            memory = "${local.config.memory}Mi"
          }
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.env
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        # Secret Manager integration
        env {
          name = "REDIS_CREDENTIALS"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.redis_credentials.secret_id
              key  = "latest"
            }
          }
        }
      }
      
      # Performance optimization
      container_concurrency = local.config.concurrency
      timeout_seconds       = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"        = local.config.min_instances
        "autoscaling.knative.dev/maxScale"        = local.config.max_instances
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.connector.id
        "run.googleapis.com/vpc-access-egress"    = "all-traffic"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
  
  depends_on = [
    google_vpc_access_connector.connector,
    google_secret_manager_secret_version.redis_credentials_version
  ]
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_service.mcp_server.location
  service  = google_cloud_run_service.mcp_server.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Monitoring dashboard
resource "google_monitoring_dashboard" "mcp_dashboard" {
  dashboard_json = <<EOF
{
  "displayName": "MCP Server Dashboard - ${var.env}",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "CPU Utilization",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}-${var.env}\" AND metric.type=\"run.googleapis.com/container/cpu/utilization\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Memory Utilization",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}-${var.env}\" AND metric.type=\"run.googleapis.com/container/memory/utilization\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Request Count",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}-${var.env}\" AND metric.type=\"run.googleapis.com/request_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Response Latency",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}-${var.env}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_PERCENTILE_99"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Instance Count",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}-${var.env}\" AND metric.type=\"run.googleapis.com/container/instance_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "Redis Memory Usage",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${var.redis_instance_name}-${var.env}\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }
          ]
        }
      }
    ]
  }
}
EOF
}

# Outputs
output "cloud_run_url" {
  value = google_cloud_run_service.mcp_server.status[0].url
  description = "The URL of the deployed Cloud Run service"
}

output "redis_host" {
  value = google_redis_instance.redis.host
  description = "Redis instance host"
  sensitive = true
}

output "redis_port" {
  value = google_redis_instance.redis.port
  description = "Redis instance port"
}

output "vpc_connector_id" {
  value = google_vpc_access_connector.connector.id
  description = "VPC Connector ID"
}