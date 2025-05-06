variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region where resources will be created"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "firestore_location" {
  description = "Location for Firestore database (if using App Engine creation method)"
  type        = string
  default     = "us-central"
}

variable "create_firestore_database" {
  description = "Whether to create the Firestore database (only needed if not already created)"
  type        = bool
  default     = false
}
