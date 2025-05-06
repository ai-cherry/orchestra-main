# AI Orchestra - Development Environment Variables
# Only include environment-specific overrides here

variable "environment" {
  description = "The deployment environment"
  type        = string
  default     = "dev"
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
  default     = "ai-cherry"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "orchestra-main"
}

variable "image_tag" {
  description = "The image tag to deploy for Cloud Run services"
  type        = string
  default     = "dev"
}

# Import core variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "project_number" {
  description = "The GCP project number"
  type        = string
  default     = "525398941159"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-west4"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 5
}

variable "cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "1000m"
}

variable "memory" {
  description = "Memory allocation for Cloud Run"
  type        = string
  default     = "2Gi"
}

variable "redis_tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC"
}

variable "redis_memory_size" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

variable "subnet_range" {
  description = "IP CIDR range for the subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "vpc_connector_range" {
  description = "IP CIDR range for the VPC connector"
  type        = string
  default     = "10.8.0.0/28"
}

variable "redis_ip_range" {
  description = "IP CIDR range for Redis"
  type        = string
  default     = "10.0.0.0/29"
}