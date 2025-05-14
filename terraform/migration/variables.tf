# variables.tf
# Consolidated variables for AI Orchestra GCP Migration

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "GCP Region for resources"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "zone" {
  description = "GCP Zone for zonal resources"
  type        = string
  default     = "us-central1-a"
}

variable "service_prefix" {
  description = "Prefix for service names"
  type        = string
  default     = "ai-orchestra"
}

variable "location" {
  description = "Location for resources that use location instead of region"
  type        = string
  default     = "us-central1"
}

# Authentication and security variables
variable "service_account_id" {
  description = "Service account ID for Cloud Run services"
  type        = string
  default     = "ai-orchestra-sa"
}

variable "github_owner" {
  description = "GitHub organization or user that owns the repositories"
  type        = string
  default     = "ai-orchestra-org"
}

variable "workload_identity_pool_id" {
  description = "Workload Identity Pool ID for GitHub Actions"
  type        = string
  default     = "github-pool"
}

# Network settings
variable "vpc_connector_name" {
  description = "Name of the VPC connector for serverless resources"
  type        = string
  default     = "ai-orchestra-vpc-connector"
}

variable "vpc_network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "ai-orchestra-network"
}

# Cloud Run settings
variable "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "ai-orchestra-api"
}

variable "container_concurrency" {
  description = "Maximum requests per container instance"
  type        = number
  default     = 80
}

variable "min_instances" {
  description = "Minimum number of container instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of container instances"
  type        = number
  default     = 10
}

variable "cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation for Cloud Run"
  type        = string
  default     = "2Gi"
}

variable "timeout_seconds" {
  description = "Request timeout for Cloud Run"
  type        = number
  default     = 300
}

# Database settings
variable "database_tier" {
  description = "Machine type for AlloyDB instance"
  type        = string
  default     = "db-standard-2"
}

variable "database_version" {
  description = "Database version for AlloyDB"
  type        = string
  default     = "POSTGRES_14"
}

# Monitoring settings
variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}