# Variables for Vertex AI Vector Search Module

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-west4"
}

variable "index_name_prefix" {
  description = "Prefix for the index name"
  type        = string
  default     = "orchestra"
}

variable "embedding_dimensions" {
  description = "Dimensions of the embedding vectors"
  type        = number
  default     = 768  # Default for text-embedding-ada-002
}

variable "approximate_neighbors_count" {
  description = "Number of approximate neighbors to return"
  type        = number
  default     = 20
}

variable "distance_measure_type" {
  description = "Distance measure type for vector similarity"
  type        = string
  default     = "COSINE"
  validation {
    condition     = contains(["COSINE", "DOT_PRODUCT", "EUCLIDEAN"], var.distance_measure_type)
    error_message = "Distance measure type must be one of: COSINE, DOT_PRODUCT, EUCLIDEAN."
  }
}

variable "leaf_node_embedding_count" {
  description = "Number of embeddings per leaf node"
  type        = number
  default     = 1000
}

variable "leaf_nodes_to_search_percent" {
  description = "Percentage of leaf nodes to search"
  type        = number
  default     = 10
}

variable "machine_type" {
  description = "Machine type for the deployed index"
  type        = string
  default     = "e2-standard-2"
}

variable "min_replica_count" {
  description = "Minimum number of replicas"
  type        = number
  default     = 1
}

variable "max_replica_count" {
  description = "Maximum number of replicas"
  type        = number
  default     = 2
}

variable "network_id" {
  description = "VPC network ID for private connectivity (optional)"
  type        = string
  default     = ""
}

variable "service_account_email" {
  description = "Service account email that will access the index endpoint"
  type        = string
}

variable "force_destroy_bucket" {
  description = "Whether to force destroy the bucket even if it contains objects"
  type        = bool
  default     = false
}