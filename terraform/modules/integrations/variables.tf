/**
 * Variables for the Orchestra integrations infrastructure module.
 */

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "prefix" {
  description = "Resource name prefix"
  type        = string
  default     = "orchestra"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "redis_tier" {
  description = "Redis memory cache tier"
  type        = string
  default     = "STANDARD_HA"
}

variable "redis_memory_size_gb" {
  description = "Redis memory cache size in GB"
  type        = number
  default     = 10
}

variable "network" {
  description = "VPC network to use for resources"
  type        = string
  default     = "default"
}

variable "alloydb_primary_cpu_count" {
  description = "CPU count for AlloyDB primary instance"
  type        = number
  default     = 8
}

variable "alloydb_replica_cpu_count" {
  description = "CPU count for AlloyDB replica instances"
  type        = number
  default     = 4
}

variable "alloydb_replica_count" {
  description = "Number of AlloyDB read replicas to create"
  type        = number
  default     = 3
}

variable "kms_key" {
  description = "KMS key for encrypting sensitive data"
  type        = string
}

variable "bigquery_location" {
  description = "Location for BigQuery datasets"
  type        = string
  default     = "US"
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

variable "github_repo" {
  description = "GitHub repository path (org/repo) for workload identity"
  type        = string
}

variable "billing_account" {
  description = "Billing account ID for budget monitoring"
  type        = string
}

variable "monthly_budget" {
  description = "Monthly budget in USD for the memory system"
  type        = string
  default     = "500"
}

variable "gemini_api_key" {
  description = "Gemini API key for LLM operations (set as null to use Secret Manager)"
  type        = string
  default     = null
  sensitive   = true
}

variable "superagi_api_key" {
  description = "SuperAGI API key for agent management (set as null to use Secret Manager)"
  type        = string
  default     = null
  sensitive   = true
}

variable "enable_gemini_context_manager" {
  description = "Enable Gemini Context Manager for 2M token context window"
  type        = bool
  default     = true
}

variable "enable_superagi_integration" {
  description = "Enable SuperAGI integration for cloud agent management"
  type        = bool
  default     = false
}

variable "enable_autogen_integration" {
  description = "Enable AutoGen integration for multi-agent conversation protocols"
  type        = bool
  default     = false
}

variable "enable_langchain_integration" {
  description = "Enable LangChain integration for enhanced memory capabilities"
  type        = bool
  default     = false
}

variable "enable_vertex_ai_integration" {
  description = "Enable Vertex AI Agent Builder integration for enterprise features"
  type        = bool
  default     = true
}
