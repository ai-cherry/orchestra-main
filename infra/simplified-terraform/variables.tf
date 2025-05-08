/**
 * Orchestra Infrastructure Variables
 *
 * This file defines the variables used in the Terraform configuration.
 */

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "The GCP region to deploy resources to"
  type        = string
  default     = "us-west4"
}

variable "zone" {
  description = "The GCP zone to deploy resources to"
  type        = string
  default     = "us-west4-a"
}

variable "env" {
  description = "The environment (dev, stage, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "The env value must be one of: dev, stage, prod."
  }
}

# Redis configuration variables
variable "redis_memory_size_gb" {
  description = "Memory size for Redis instance in GB"
  type        = number
  default     = 5
  
  validation {
    condition     = var.redis_memory_size_gb >= 1 && var.redis_memory_size_gb <= 32
    error_message = "Redis memory size must be between 1 and 32 GB."
  }
}

variable "redis_version" {
  description = "Redis version to use"
  type        = string
  default     = "REDIS_6_X"
  
  validation {
    condition     = contains(["REDIS_6_X", "REDIS_5_0", "REDIS_4_0"], var.redis_version)
    error_message = "Redis version must be one of: REDIS_6_X, REDIS_5_0, REDIS_4_0."
  }
}

# PostgreSQL configuration variables
variable "postgres_tier" {
  description = "The machine type to use for PostgreSQL"
  type        = string
  default     = "db-g1-small"
}

variable "postgres_availability_type" {
  description = "The availability type for PostgreSQL (REGIONAL or ZONAL)"
  type        = string
  default     = "ZONAL"
  
  validation {
    condition     = contains(["REGIONAL", "ZONAL"], var.postgres_availability_type)
    error_message = "PostgreSQL availability type must be one of: REGIONAL, ZONAL."
  }
}

variable "postgres_max_connections" {
  description = "Maximum number of connections for PostgreSQL"
  type        = number
  default     = 200
  
  validation {
    condition     = var.postgres_max_connections >= 10 && var.postgres_max_connections <= 1000
    error_message = "PostgreSQL max connections must be between 10 and 1000."
  }
}

variable "postgres_work_mem" {
  description = "Work memory for PostgreSQL"
  type        = string
  default     = "16MB"
}

variable "postgres_maintenance_mem" {
  description = "Maintenance work memory for PostgreSQL"
  type        = string
  default     = "128MB"
}