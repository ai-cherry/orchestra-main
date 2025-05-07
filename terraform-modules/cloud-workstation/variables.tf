# Variables for Cloud Workstation Module

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "The GCP region where the workstation will be deployed"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Name for the Cloud Workstation cluster"
  type        = string
  default     = "ai-development"
}

variable "config_name" {
  description = "Name for the Cloud Workstation configuration"
  type        = string
  default     = "ai-dev-config"
}

variable "workstation_name" {
  description = "Name for the Cloud Workstation instance"
  type        = string
  default     = "ai-workstation"
}

variable "network_name" {
  description = "The VPC network to use for the workstation"
  type        = string
  default     = "default"
}

variable "subnetwork_name" {
  description = "The VPC subnetwork to use for the workstation"
  type        = string
  default     = "default"
}

variable "private_endpoint_enabled" {
  description = "Whether to enable private endpoint for the cluster"
  type        = bool
  default     = false
}

variable "disable_public_ip" {
  description = "Whether to disable public IP addresses for the workstation"
  type        = bool
  default     = false
}

variable "environment_variables" {
  description = "Environment variables to set in the workstation container"
  type        = map(string)
  default     = {
    "JUPYTER_PORT" = "8888",
    "VERTEX_PROJECT" = "cherry-ai-project",
    "VERTEX_LOCATION" = "us-central1"
  }
}

variable "gpu_type" {
  description = "Type of GPU to use for the workstation"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "gpu_count" {
  description = "Number of GPUs to use for the workstation"
  type        = number
  default     = 2
}

variable "persistent_disk_size_gb" {
  description = "Size of the persistent disk in GB"
  type        = number
  default     = 1024  # 1TB
}

variable "boot_disk_size_gb" {
  description = "Size of the boot disk in GB"
  type        = number
  default     = 100
}

variable "machine_type" {
  description = "Machine type for the workstation"
  type        = string
  default     = "n2d-standard-32"
}

variable "tags" {
  description = "Tags to apply to the workstation resources"
  type        = map(string)
  default     = {
    "environment" = "development",
    "purpose"     = "ai-development"
  }
}
