# AI Orchestra Terraform variables
# Comprehensive variable definitions for GCP infrastructure

# Project Configuration
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "project_prefix" {
  description = "Prefix used for naming resources"
  type        = string
  default     = "ai-orchestra"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "The GCP region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone within the region"
  type        = string
  default     = "us-central1-a"
}

variable "service_prefix" {
  description = "Prefix used for service naming"
  type        = string
  default     = "orchestra"
}

# Container and Repository Configuration
variable "image_repository" {
  description = "Container image repository path"
  type        = string
  default     = "gcr.io/cherry-ai-project"
}

variable "image_tag" {
  description = "Container image tag to deploy"
  type        = string
  default     = "latest"
}

# Service Configuration: Admin API
variable "admin_api_env_vars" {
  description = "Environment variables for Admin API"
  type        = map(string)
  default     = {
    PORT                       = "8080"
    LOG_LEVEL                  = "info"
    CONTEXT_OPTIMIZATION_LEVEL = "maximum"
  }
}

variable "admin_api_secret_env_vars" {
  description = "Secret environment variables for Admin API"
  type        = map(object({
    secret_name = string
    secret_key  = string
  }))
  default     = {}
}

variable "container_concurrency_settings" {
  description = "Container concurrency for each service"
  type        = map(number)
  default     = {
    admin_api = 80
  }
}

variable "cpu_limits" {
  description = "CPU limits for each service"
  type        = map(string)
  default     = {
    admin_api = "4"
  }
}

variable "memory_limits" {
  description = "Memory limits for each service"
  type        = map(string)
  default     = {
    admin_api = "2Gi"
  }
}

variable "min_instances" {
  description = "Minimum instances for each service"
  type        = map(number)
  default     = {
    admin_api = 1
  }
}

variable "max_instances" {
  description = "Maximum instances for each service"
  type        = map(number)
  default     = {
    admin_api = 10
  }
}

# Service Accounts
variable "service_accounts" {
  description = "Service accounts for each service"
  type        = map(string)
  default     = {
    admin_api = "admin-api-sa@cherry-ai-project.iam.gserviceaccount.com"
  }
}

variable "service_account_roles" {
  description = "IAM roles to assign to service accounts"
  type        = list(string)
  default     = [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor"
  ]
}

# Network Configuration
variable "vpc_connector_name" {
  description = "Name of the VPC connector for Cloud Run"
  type        = string
  default     = "orchestra-vpc-connector"
}

variable "ip_cidr_range" {
  description = "IP CIDR range for the subnet"
  type        = string
  default     = "10.0.0.0/28"
}

# Database Configuration
variable "cloudsql_connections" {
  description = "CloudSQL connections for each service"
  type        = map(string)
  default     = {
    admin_api = ""
  }
}

# Domain Configuration
variable "enable_custom_domains" {
  description = "Whether to enable custom domains"
  type        = bool
  default     = false
}

variable "domain_mappings" {
  description = "Custom domain mappings for services"
  type        = map(string)
  default     = {
    admin_api = "api.orchestra.example.com"
  }
}

# Security Configuration
variable "make_admin_api_public" {
  description = "Whether to make the Admin API publicly accessible"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Whether to enable Cloud Monitoring"
  type        = bool
  default     = true
}

variable "notification_channels" {
  description = "Notification channels for alerts"
  type        = map(string)
  default     = {
    email = "projects/cherry-ai-project/notificationChannels/email-channel"
  }
}

# Workstation Configuration
variable "enable_gpu" {
  description = "Whether to enable GPU for workstations"
  type        = bool
  default     = true
}

variable "secret_name_prefix" {
  description = "Prefix for secret names"
  type        = string
  default     = "ai-orchestra"
}
variable "org" {
  description = "The organization name for the project."
  type        = string
}
variable "env" {
  description = "The deployment environment (e.g., dev, staging, prod)."
  type        = string
}