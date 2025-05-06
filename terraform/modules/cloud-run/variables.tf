# Variables for the Cloud Run module

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy to"
  type        = string
}

variable "env" {
  description = "The environment (e.g., dev, staging, prod)"
  type        = string
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
}

variable "container_image" {
  description = "The container image to deploy"
  type        = string
}

variable "cpu" {
  description = "The CPU allocation for the Cloud Run service"
  type        = string
  default     = "1000m"
}

variable "memory" {
  description = "The memory allocation for the Cloud Run service"
  type        = string
  default     = "512Mi"
}

variable "environment_variables" {
  description = "Environment variables to set in the container"
  type        = map(string)
  default     = {}
}

variable "secret_environment_variables" {
  description = "Secret environment variables to set in the container"
  type        = map(object({
    secret_name = string
    secret_key  = string
  }))
  default     = {}
}

variable "container_port" {
  description = "The port the container listens on"
  type        = number
  default     = 8080
}

variable "service_account_email" {
  description = "The service account email to run the service as"
  type        = string
}

variable "container_concurrency" {
  description = "The maximum number of concurrent requests per container"
  type        = number
  default     = 80
}

variable "timeout_seconds" {
  description = "The maximum time a request can take before timing out"
  type        = number
  default     = 300
}

variable "min_instances" {
  description = "The minimum number of instances to keep running"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "The maximum number of instances to scale to"
  type        = number
  default     = 100
}

variable "public_access" {
  description = "Whether to allow public access to the service"
  type        = bool
  default     = false
}

variable "invoker_members" {
  description = "IAM members who can invoke the service when public_access is false"
  type        = list(string)
  default     = []
}

variable "domain_name" {
  description = "The domain name to map to the service"
  type        = string
  default     = ""
}

variable "secrets" {
  description = "Map of secrets to create in Secret Manager"
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "scheduler_config" {
  description = "Configuration for Cloud Scheduler job"
  type = object({
    schedule             = string
    http_method          = string
    service_account_email = string
  })
  default = null
}

variable "enable_monitoring" {
  description = "Whether to enable Cloud Monitoring alerting"
  type        = bool
  default     = false
}

variable "error_rate_threshold" {
  description = "Threshold for error rate alerting"
  type        = number
  default     = 0.05
}

variable "notification_channels" {
  description = "Notification channels for alerting"
  type        = list(string)
  default     = []
}