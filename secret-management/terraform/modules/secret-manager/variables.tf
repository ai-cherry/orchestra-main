/**
 * # Variables for Secret Manager Module
 *
 * Configuration variables for the Secret Manager module
 */

variable "project_id" {
  description = "The GCP project ID where secrets will be stored"
  type        = string
}

variable "secrets" {
  description = "Map of secrets to create with their configurations"
  type = map(object({
    labels          = optional(map(string), {})
    initial_value   = optional(string)
    rotation_period = optional(string)
    expiration      = optional(string)
    access = map(object({
      members = list(string)
      condition = optional(object({
        title       = string
        description = string
        expression  = string
      }))
    }))
  }))
  
  validation {
    condition     = length(var.secrets) > 0
    error_message = "At least one secret must be defined."
  }
}

variable "labels" {
  description = "A set of key/value label pairs to assign to the secret"
  type        = map(string)
  default     = {}
}

variable "replication_automatic" {
  description = "Use automatic replication (true) or user-managed (false)"
  type        = bool
  default     = true
}

variable "replication_locations" {
  description = "The locations to replicate secrets to when using user-managed replication"
  type        = list(string)
  default     = ["us-central1", "us-east1"]
}

variable "customer_managed_encryption_key" {
  description = "The KMS key to use for encrypting the secret data (optional)"
  type        = string
  default     = ""
}

variable "default_access_roles" {
  description = "Default roles to apply to all secrets if not specified in the secret config"
  type        = list(string)
  default     = ["roles/secretmanager.secretAccessor"]
}

variable "default_access_members" {
  description = "Default members to grant access to all secrets if not specified in the secret config"
  type        = list(string)
  default     = []
}
