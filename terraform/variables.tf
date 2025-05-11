# Variables for AI Orchestra performance-optimized deployment
# This file centralizes all variables for better organization and reusability

# Project variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_number" {
  description = "The GCP project number"
  type        = string
  default     = ""
}

variable "region" {
  description = "The GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "The environment must be one of: dev, staging, prod."
  }
}

# Service account variables
variable "service_account_name" {
  description = "The name of the service account for Cloud Run"
  type        = string
  default     = "ai-orchestra-sa"
}

variable "orchestrator_service_account" {
  description = "Service account for the Orchestrator API"
  type        = string
  default     = ""
}

variable "github_actions_sa" {
  description = "Service account for GitHub Actions"
  type        = string
  default     = ""
}

# Secret Manager variables
variable "secret_name_prefix" {
  description = "Prefix for Secret Manager secrets"
  type        = string
  default     = "secret-management-key"
}

# Cloud Run variables
variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run service"
  type        = string
  default     = "1000m"  # 1 vCPU
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run service"
  type        = string
  default     = "2Gi"    # 2 GB
}

variable "cloud_run_concurrency" {
  description = "Maximum number of concurrent requests per container"
  type        = number
  default     = 80
}

variable "cloud_run_timeout" {
  description = "Maximum request timeout in seconds"
  type        = number
  default     = 300  # 5 minutes
}

variable "cloud_run_min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "cloud_run_max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

# Monitoring variables
variable "latency_threshold_ms" {
  description = "Threshold for latency alerts in milliseconds"
  type        = number
  default     = 1000  # 1 second
}

# Scheduler variables
variable "scheduler_interval" {
  description = "Interval for the keep-warm scheduler job"
  type        = string
  default     = "*/5 * * * *"  # Every 5 minutes
}

# Region configuration
variable "regions" {
  description = "Map of region configurations"
  type        = map(string)
  default     = {
    default    = "us-central1"
    workstation = "us-central1"
    pubsub     = "us-central1"
  }
}