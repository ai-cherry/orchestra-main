/**
 * # Variables for Secret Rotation Module
 *
 * Configuration variables for the Secret Rotation module
 */

variable "project_id" {
  description = "The GCP project ID where resources will be created"
  type        = string
}

variable "region" {
  description = "The GCP region where resources will be created"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment identifier (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "secrets_to_rotate" {
  description = "List of secret IDs to include in the rotation schedule"
  type        = list(string)
  
  validation {
    condition     = length(var.secrets_to_rotate) > 0
    error_message = "At least one secret must be specified for rotation."
  }
}

variable "rotation_schedule" {
  description = "Cron schedule expression for when to rotate secrets"
  type        = string
  default     = "0 0 1 * *"  # Default: midnight on the 1st of every month
  
  validation {
    condition     = can(regex("^[0-9*,-/]+\\s+[0-9*,-/]+\\s+[0-9*,-/]+\\s+[0-9*,-/]+\\s+[0-9*,-/]+$", var.rotation_schedule))
    error_message = "The rotation_schedule must be a valid cron expression in 5-field format."
  }
}

variable "time_zone" {
  description = "Time zone for the rotation schedule (IANA Time Zone Database name)"
  type        = string
  default     = "Etc/UTC"
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated access to the rotation function"
  type        = bool
  default     = false
}

variable "function_memory_mb" {
  description = "Memory allocation for the Cloud Function (in MB)"
  type        = number
  default     = 256
  
  validation {
    condition     = var.function_memory_mb >= 128 && var.function_memory_mb <= 8192
    error_message = "Function memory must be between 128 MB and 8192 MB."
  }
}

variable "function_timeout" {
  description = "Timeout for the Cloud Function (in seconds)"
  type        = number
  default     = 180
  
  validation {
    condition     = var.function_timeout >= 60 && var.function_timeout <= 540
    error_message = "Function timeout must be between 60 and 540 seconds."
  }
}

variable "additional_function_permissions" {
  description = "Additional IAM roles to grant to the rotation function service account"
  type        = list(string)
  default     = []
}

variable "additional_env_vars" {
  description = "Additional environment variables for the Cloud Function"
  type        = map(string)
  default     = {}
}

variable "rotation_strategies" {
  description = "Map of secret ID to rotation strategy, defaults to 'random' if not specified"
  type        = map(string)
  default     = {}
  
  validation {
    condition     = alltrue([for s in values(var.rotation_strategies) : contains(["random", "api", "custom"], s)])
    error_message = "Rotation strategy must be one of: random, api, custom."
  }
}
