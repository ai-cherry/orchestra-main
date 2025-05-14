# Variables for GCP Workstations module

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "The GCP region where resources will be created"
  type        = string
  default     = "us-central1"
}

variable "network" {
  description = "The VPC network to use for workstations"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "The VPC subnetwork to use for workstations"
  type        = string
  default     = "default"
}

variable "machine_type" {
  description = "Machine type for workstation VMs"
  type        = string
  default     = "e2-standard-4"
}

variable "boot_disk_size_gb" {
  description = "Size of the boot disk in GB"
  type        = number
  default     = 50
}

variable "data_disk_size_gb" {
  description = "Size of the data disk in GB"
  type        = number
  default     = 100
}

variable "cache_disk_size_gb" {
  description = "Size of the cache disk in GB"
  type        = number
  default     = 20
}

variable "workstation_image_version" {
  description = "Version of the workstation container image"
  type        = string
  default     = "latest"
}

variable "idle_timeout" {
  description = "Idle timeout for workstations in seconds"
  type        = string
  default     = "3600s" # 1 hour
}

variable "running_timeout" {
  description = "Maximum running time for workstations in seconds"
  type        = string
  default     = "86400s" # 24 hours
}

variable "workstation_users" {
  description = "List of users who can access workstations (emails in format 'user:user@example.com')"
  type        = list(string)
  default     = []
}