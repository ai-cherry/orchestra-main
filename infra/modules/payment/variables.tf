/**
 * # Payment Processing Module Variables
 *
 * Variables for the payment processing infrastructure module
 */

# ------------ Project Setup --------------

variable "project_id" {
  description = "The GCP project ID to use for payment processing"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment name (dev, stage, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "Environment must be one of: dev, stage, prod"
  }
}

variable "create_project" {
  description = "Whether to create a new GCP project or use an existing one"
  type        = bool
  default     = false
}

variable "billing_account" {
  description = "The billing account ID to associate with the project (required if create_project is true)"
  type        = string
  default     = ""
}

# ------------ Service Accounts --------------

variable "service_accounts" {
  description = "Map of service accounts to create and their IAM roles"
  type        = map(object({
    roles = list(string)
  }))
  default     = {
    "payment-data-reader" = {
      roles = [
        "roles/bigquery.dataViewer", 
        "roles/firestore.viewer"
      ]
    },
    "payment-data-processor" = {
      roles = [
        "roles/bigquery.dataEditor", 
        "roles/firestore.user", 
        "roles/dataflow.worker"
      ]
    },
    "payment-reporting" = {
      roles = [
        "roles/bigquery.dataViewer",
        "roles/bigquery.jobUser"
      ]
    },
    "payment-vertex-agent" = {
      roles = [
        "roles/aiplatform.user"
      ]
    }
  }
}

# ------------ Storage Infrastructure --------------

variable "storage_buckets" {
  description = "Map of storage buckets to create for payment data"
  type        = map(object({
    location           = optional(string)
    storage_class      = optional(string)
    versioning_enabled = optional(bool)
    retention_days     = optional(number)
  }))
  default     = {
    "raw-data" = {
      retention_days = 365
    },
    "processed-data" = {
      retention_days = 180
    },
    "analytics-results" = {
      retention_days = 90
    },
    "embeddings" = {
      storage_class = "STANDARD"
    },
    "audit-logs" = {
      retention_days = 730
    }
  }
}

variable "bigquery_datasets" {
  description = "Map of BigQuery datasets to create"
  type        = map(object({
    description               = optional(string)
    location                  = optional(string)
    delete_contents_on_destroy = optional(bool)
    expiration_ms             = optional(number)
  }))
  default     = {
    "payment_raw" = {
      description = "Raw payment transaction data"
    },
    "payment_processed" = {
      description = "Processed payment data"
    },
    "payment_analytics" = {
      description = "Payment analytics datasets"
    }
  }
}

# ------------ Vertex AI --------------

variable "vertex_endpoints" {
  description = "Map of Vertex AI endpoints for payment analysis"
  type        = map(object({
    description = optional(string)
    location    = optional(string)
    min_replica_count = optional(number)
    max_replica_count = optional(number)
  }))
  default     = {
    "payment-fraud-detection" = {
      description = "Endpoint for payment fraud detection"
      min_replica_count = 1
      max_replica_count = 3
    },
    "payment-trend-analysis" = {
      description = "Endpoint for payment trend analysis"
      min_replica_count = 1
      max_replica_count = 2
    }
  }
}

variable "enable_vector_search" {
  description = "Whether to enable Vertex AI Vector Search for payment patterns"
  type        = bool
  default     = true
}

variable "vector_dimension" {
  description = "Dimension size for vector embeddings"
  type        = number
  default     = 1536  # Default for OpenAI embedding models
}

# ------------ Security Controls --------------

variable "enable_cmek" {
  description = "Whether to enable Customer-Managed Encryption Keys"
  type        = bool
  default     = true
}

variable "enable_vpc_sc" {
  description = "Whether to enable VPC Service Controls for the payment project"
  type        = bool
  default     = false
}

variable "access_policy_id" {
  description = "Access Context Manager policy ID for VPC SC (required if enable_vpc_sc is true)"
  type        = string
  default     = ""
}

variable "audit_log_retention_days" {
  description = "Number of days to retain audit logs. Set to 0 to disable audit log sink."
  type        = number
  default     = 365
}

# ------------ Pub/Sub --------------

variable "enable_pubsub_schemas" {
  description = "Whether to enable Pub/Sub schemas for payment events"
  type        = bool
  default     = true
}

# ------------ Cloud Functions --------------

variable "deploy_functions" {
  description = "Whether to deploy Cloud Functions for payment processing"
  type        = bool
  default     = false
}

variable "function_source_zip_path" {
  description = "Path to the zip file containing function source code. If empty, a placeholder is used."
  type        = string
  default     = ""
}
