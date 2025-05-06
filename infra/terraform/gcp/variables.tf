variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai.me"
}

variable "project_number" {
  description = "The GCP project number"
  type        = string
  default     = "525398941159"
}

variable "region" {
  description = "The GCP region where resources will be created"
  type        = string
  default     = "us-central1"
}

variable "service_account_id" {
  description = "The ID of the service account to use"
  type        = string
  default     = "vertex-agent"
}

variable "registry_name" {
  description = "The name of the Artifact Registry repository"
  type        = string
  default     = "orchestra"
}

variable "container_image" {
  description = "The container image path in Artifact Registry"
  type        = string
  default     = "us-central1-docker.pkg.dev/cherry-ai.me/orchestra/api"
}

variable "storage_bucket_prefix" {
  description = "Prefix for GCS bucket names"
  type        = string
  default     = "cherry-ai-me"
}

variable "environment" {
  description = "The deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}