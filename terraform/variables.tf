# Variables for the GCP Workstations Terraform configuration
# Performance-optimized for GitHub Codespaces to GCP Workstations migration

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for deployments"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for zonal resources"
  type        = string
  default     = "us-central1-a"
}

variable "project_prefix" {
  description = "Prefix for naming resources"
  type        = string
  default     = "ai-orchestra"
}

variable "enable_gpu" {
  description = "Enable GPU for workstations"
  type        = bool
  default     = true
}

variable "gpu_type" {
  description = "GPU type to use when enable_gpu is true"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "gpu_count" {
  description = "Number of GPUs to attach when enable_gpu is true"
  type        = number
  default     = 1
}

variable "standard_machine_type" {
  description = "Machine type for standard development workstations"
  type        = string
  default     = "e2-standard-8"
}

variable "ml_machine_type" {
  description = "Machine type for ML-optimized workstations"
  type        = string
  default     = "n1-standard-16"
}

variable "boot_disk_size_gb" {
  description = "Size of the boot disk in GB"
  type        = number
  default     = 100
}

variable "persistent_disk_size_gb" {
  description = "Size of the persistent disk in GB"
  type        = number
  default     = 200
}

variable "disable_public_ip" {
  description = "Disable public IP address for workstations"
  type        = bool
  default     = false  # Set to false for better performance, easier access
}

variable "auto_shutdown_minutes" {
  description = "Automatically shut down workstations after this many minutes of inactivity"
  type        = number
  default     = 20
}

variable "performance_optimized" {
  description = "Enable performance optimizations"
  type        = bool
  default     = true
}

variable "ip_cidr_range" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.2.0.0/16"
}

variable "container_image" {
  description = "Container image for workstations"
  type        = string
  default     = "us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest"
}

variable "environment_variables" {
  description = "Environment variables to set in the workstation"
  type        = map(string)
  default     = {}
}

variable "enable_monitoring" {
  description = "Enable Cloud Monitoring for workstations"
  type        = bool
  default     = true
}

variable "service_account_roles" {
  description = "Roles to assign to the workstation service account"
  type        = list(string)
  default     = [
    "roles/editor",                   # For performance over security in single-dev project
    "roles/aiplatform.user",          # For Vertex AI integration
    "roles/secretmanager.secretAccessor", # For accessing secrets
    "roles/storage.objectAdmin",      # For accessing GCS
    "roles/logging.logWriter",        # For writing logs
    "roles/monitoring.metricWriter",  # For writing metrics
  ]
}