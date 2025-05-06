variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for resources."
  type        = string
  default     = "us-west4"
}

variable "environment" {
  description = "Deployment environment (prod or staging)."
  type        = string
  default     = "staging"
  
  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "Environment must be one of: prod, staging, dev."
  }
}

variable "service_name" {
  description = "Base name for the service."
  type        = string
  default     = "orchestra"
}

variable "memory_ttl" {
  description = "TTL for short-term memory in seconds."
  type        = number
  default     = 3600 # 1 hour
}

variable "redis_memory_size_gb" {
  description = "Memory size for Redis instance in GB."
  type        = number
  default     = 1
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances."
  type        = number
  default     = 10
}

variable "cpu" {
  description = "CPU allocation for Cloud Run instances."
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation for Cloud Run instances."
  type        = string
  default     = "1Gi"
}

variable "container_image" {
  description = "Container image to deploy."
  type        = string
  default     = null
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service."
  type        = bool
  default     = true
}

variable "vpc_connector" {
  description = "VPC connector for the service."
  type        = string
  default     = null
}

variable "vpc_egress" {
  description = "VPC egress setting for the service."
  type        = string
  default     = "private-ranges-only"
}

variable "service_account_create" {
  description = "Whether to create a new service account."
  type        = bool
  default     = true
}

variable "service_account_name" {
  description = "Name of the service account to use."
  type        = string
  default     = "orchestra-service-account"
}

variable "service_account_roles" {
  description = "IAM roles to assign to the service account."
  type        = list(string)
  default = [
    "roles/secretmanager.secretAccessor",
    "roles/firestore.user",
    "roles/redis.editor",
    "roles/storage.objectUser",
    "roles/aiplatform.user"
  ]
}

variable "create_secrets" {
  description = "Whether to create Secret Manager secrets."
  type        = bool
  default     = true
}

variable "secrets" {
  description = "Map of secrets to create."
  type        = map(string)
  default = {
    "openai-api-key"    = "Secret for OpenAI API key"
    "anthropic-api-key" = "Secret for Anthropic API key"
    "gemini-api-key"    = "Secret for Gemini API key"
  }
}

variable "env_vars" {
  description = "Environment variables to set on the service."
  type        = map(string)
  default     = {}
}

variable "secret_env_vars" {
  description = "Secret environment variables to set on the service."
  type        = map(object({
    secret_id  = string
    version_id = string
  }))
  default = {}
}