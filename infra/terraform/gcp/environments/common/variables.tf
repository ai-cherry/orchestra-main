/**
 * Variables for the Orchestra project common environment
 */

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "The GCP region where resources will be created"
  type        = string
  default     = "us-west4"
}

variable "env" {
  description = "Environment name (common, dev, prod)"
  type        = string
  default     = "common"
}

variable "github_repo" {
  description = "GitHub repository for Workload Identity Federation"
  type        = string
  default     = "ai-cherry/orchestra-main"
}

variable "redis_memory_size_gb" {
  description = "Memory size for Redis instance in GB"
  type        = number
  default     = 1
}

variable "firestore_location" {
  description = "Location for Firestore database"
  type        = string
  default     = "nam5"
}

variable "vector_search_dimensions" {
  description = "Dimensions for vector search embeddings"
  type        = number
  default     = 768
}

variable "enable_deletion_protection" {
  description = "Whether to enable deletion protection for resources"
  type        = bool
  default     = true
}
