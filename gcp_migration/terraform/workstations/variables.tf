/**
 * Variables for GCP Workstations Terraform module
 * 
 * This file defines the variables used in the GCP Workstations Terraform module.
 */

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "The GCP region for the workstation cluster"
  type        = string
  default     = "us-west4"
}

variable "network_name" {
  description = "VPC network name (will be created if it doesn't exist)"
  type        = string
  default     = "workstation-network"
}

variable "subnet_name" {
  description = "Subnet name (will be created if it doesn't exist)"
  type        = string
  default     = "workstation-subnet"
}

variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.10.0.0/20"
}

variable "workstation_cluster_id" {
  description = "ID for the workstation cluster"
  type        = string
  default     = "orchestra-cluster"
}

variable "standard_config_id" {
  description = "ID for the standard workstation configuration"
  type        = string
  default     = "orchestra-standard-config"
}

variable "ml_config_id" {
  description = "ID for the ML workstation configuration"
  type        = string
  default     = "orchestra-ml-config"
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB for workstations"
  type        = number
  default     = 100
}

variable "persistent_disk_size_gb" {
  description = "Persistent disk size in GB for workstations"
  type        = number
  default     = 200
}

variable "standard_machine_type" {
  description = "Machine type for standard workstations"
  type        = string
  default     = "e2-standard-8"
}

variable "ml_machine_type" {
  description = "Machine type for ML workstations"
  type        = string
  default     = "n1-standard-8"
}

variable "standard_container_image" {
  description = "Container image for standard workstations"
  type        = string
  default     = "us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest"
}

variable "ml_container_image" {
  description = "Container image for ML workstations"
  type        = string
  default     = "us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest"
}

variable "enable_public_ip" {
  description = "Whether to enable public IP addresses for workstations"
  type        = bool
  default     = true
}

variable "enable_gpu" {
  description = "Whether to enable GPU for ML workstations"
  type        = bool
  default     = true
}

variable "gpu_type" {
  description = "GPU type for ML workstations"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "gpu_count" {
  description = "Number of GPUs for ML workstations"
  type        = number
  default     = 1
}

variable "service_account_roles" {
  description = "IAM roles to assign to the workstation service account"
  type        = list(string)
  default = [
    "roles/artifactregistry.reader",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/storage.objectViewer",
    "roles/secretmanager.secretAccessor"
  ]
}

variable "allowed_cidrs" {
  description = "List of CIDR ranges allowed to connect to workstations"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Allow from anywhere - restrict for production
}

variable "idle_timeout_minutes" {
  description = "Idle timeout in minutes for workstations"
  type        = number
  default     = 30
}

variable "running_timeout_minutes" {
  description = "Maximum running time in minutes for workstations"
  type        = number
  default     = 1440  # 24 hours
}

variable "enable_secure_boot" {
  description = "Whether to enable secure boot for workstations"
  type        = bool
  default     = true
}

variable "enable_auto_suspend" {
  description = "Whether to enable automatic suspension for idle workstations"
  type        = bool
  default     = true
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default = {
    "managed-by" = "terraform"
    "project"    = "ai-orchestra"
  }
}