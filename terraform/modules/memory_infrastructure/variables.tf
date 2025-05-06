/**
 * # Memory Infrastructure Module Variables
 *
 * This file defines the input variables for the memory infrastructure module.
 */

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-west4"
}

variable "environment" {
  description = "The environment (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "redis_tier" {
  description = "The Redis instance tier"
  type        = string
  default     = "BASIC"
  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be either BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size_gb" {
  description = "The Redis instance memory size in GB"
  type        = number
  default     = 1
  validation {
    condition     = var.redis_memory_size_gb >= 1 && var.redis_memory_size_gb <= 32
    error_message = "Redis memory size must be between 1 and 32 GB."
  }
}

variable "vector_dimension" {
  description = "The dimension of the embedding vectors for Vertex AI Vector Search"
  type        = number
  default     = 768
  validation {
    condition     = var.vector_dimension > 0
    error_message = "Vector dimension must be a positive number."
  }
}

variable "storage_bucket" {
  description = "The GCS bucket for storing vector embeddings"
  type        = string
}

variable "network" {
  description = "The VPC network for private connectivity"
  type        = string
  default     = "default"
}

variable "service_account_email" {
  description = "The service account email that will access the memory resources"
  type        = string
}

variable "enable_private_connectivity" {
  description = "Whether to enable private connectivity for Redis and Vertex AI"
  type        = bool
  default     = false
}

variable "firestore_collections" {
  description = "The Firestore collections to create for memory storage"
  type        = list(string)
  default     = ["orchestra_short_term", "orchestra_mid_term", "orchestra_long_term", "orchestra_semantic"]
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}