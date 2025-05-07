/**
 * Payment Processing Infrastructure Example
 *
 * This example demonstrates how to deploy the payment processing infrastructure
 * module to set up a secure environment for payment data analysis.
 */

provider "google" {
  project = "cherry-ai-project"  # Parent/billing project
  region  = "us-west2"
}

provider "google-beta" {
  project = "cherry-ai-project"  # Parent/billing project
  region  = "us-west2"
}

# Create the payment processing infrastructure in a separate project
module "payment_processing" {
  source = "../modules/payment"
  
  # Project configuration
  project_id     = "payment-processing-dev"
  region         = "us-west2"
  env            = "dev"
  create_project = true
  billing_account = "BILLING-ACCOUNT-ID"  # Replace with actual billing account ID
  
  # Security features - Enable all for production
  enable_cmek    = true
  enable_vpc_sc  = false  # Set to true for production after creating Access Context Manager policy
  access_policy_id = ""   # Required when enable_vpc_sc = true
  
  # Customize service account roles if needed
  service_accounts = {
    "payment-data-reader" = {
      roles = [
        "roles/bigquery.dataViewer", 
        "roles/firestore.viewer",
        "roles/storage.objectViewer"
      ]
    },
    "payment-data-processor" = {
      roles = [
        "roles/bigquery.dataEditor", 
        "roles/firestore.user", 
        "roles/dataflow.worker",
        "roles/storage.objectUser"
      ]
    },
    "payment-reporting" = {
      roles = [
        "roles/bigquery.dataViewer",
        "roles/bigquery.jobUser",
        "roles/bigquery.readSessionUser"
      ]
    },
    "payment-vertex-agent" = {
      roles = [
        "roles/aiplatform.user"
      ]
    }
  }
  
  # Storage buckets for payment data
  storage_buckets = {
    "raw-data" = {
      retention_days = 365,
      location = "us-west2"
    },
    "processed-data" = {
      retention_days = 180,
      location = "us-west2"
    },
    "analytics-results" = {
      retention_days = 90,
      location = "us-west2"
    },
    "embeddings" = {
      storage_class = "STANDARD",
      location = "us-west2"
    },
    "audit-logs" = {
      retention_days = 730,
      location = "us"  # Multi-region for better durability of audit logs
    }
  }
  
  # BigQuery datasets for payment analytics
  bigquery_datasets = {
    "payment_raw" = {
      description = "Raw payment transaction data",
      location = "us-west2"
    },
    "payment_processed" = {
      description = "Processed payment data for analysis",
      location = "us-west2"
    },
    "payment_analytics" = {
      description = "Payment analytics datasets and views",
      location = "us-west2",
      delete_contents_on_destroy = false
    },
    "payment_ml_features" = {
      description = "Feature tables for payment ML models",
      location = "us-west2"
    }
  }
  
  # Enable Vertex AI features for analysis
  enable_vector_search = true
  vector_dimension = 1536  # OpenAI embedding dimension
  
  # Vertex AI endpoints for specialized analysis
  vertex_endpoints = {
    "payment-fraud-detection" = {
      description = "Endpoint for payment fraud detection models",
      min_replica_count = 1,
      max_replica_count = 3
    },
    "payment-trend-analysis" = {
      description = "Endpoint for payment trend analysis models",
      min_replica_count = 1,
      max_replica_count = 2
    },
    "payment-categorization" = {
      description = "Endpoint for transaction categorization models",
      min_replica_count = 1,
      max_replica_count = 2
    }
  }
  
  # Enable Pub/Sub schemas for structured events
  enable_pubsub_schemas = true
  
  # Audit logging configuration
  audit_log_retention_days = 365
}

# Output the key resources created
output "payment_project_id" {
  description = "The payment processing project ID"
  value       = module.payment_processing.project_id
}

output "payment_service_accounts" {
  description = "The payment processing service accounts"
  value       = module.payment_processing.service_account_emails
}

output "payment_storage_buckets" {
  description = "The storage buckets for payment data"
  value       = module.payment_processing.storage_bucket_names
}

output "payment_bigquery_datasets" {
  description = "The BigQuery datasets for payment analytics"
  value       = module.payment_processing.bigquery_dataset_ids
}

output "payment_pubsub_topic" {
  description = "The Pub/Sub topic for payment events"
  value       = module.payment_processing.pubsub_topic
}

output "payment_vertex_endpoints" {
  description = "The Vertex AI endpoints for payment analysis"
  value       = module.payment_processing.vertex_endpoints
}
