/**
 * Terraform configuration for Orchestra integration infrastructure.
 * This module sets up the necessary infrastructure for integrating
 * SuperAGI, AutoGen, LangChain, and Vertex AI with Orchestra.
 */

# Configure Google provider
provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  service_account_name = "${var.prefix}-integrations-sa"
  redis_instance_name  = "${var.prefix}-memory-cache"
  alloydb_cluster_name = "${var.prefix}-memory-db"
  bq_dataset_id        = "${var.prefix}_memory_analytics"
}

# Service account for integrations
resource "google_service_account" "integrations_sa" {
  account_id   = local.service_account_name
  display_name = "Orchestra Integrations Service Account"
  description  = "Service account for Orchestra integration components"
}

# Grant necessary permissions
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.integrations_sa.email}"
}

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.integrations_sa.email}"
}

resource "google_project_iam_member" "secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.integrations_sa.email}"
}

# Redis instance for real-time memory layer
resource "google_redis_instance" "memory_cache" {
  name           = local.redis_instance_name
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb
  
  region                  = var.region
  authorized_network      = var.network
  redis_version           = "REDIS_6_X"
  display_name            = "Orchestra Memory Cache"
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 2
        minutes = 0
      }
    }
  }
}

# AlloyDB cluster for persistent memory layer
resource "google_alloydb_cluster" "memory_db" {
  cluster_id = local.alloydb_cluster_name
  location   = var.region
  network    = var.network
  
  labels = {
    environment = var.environment
    application = "orchestra"
  }
}

# AlloyDB primary instance
resource "google_alloydb_instance" "primary" {
  cluster       = google_alloydb_cluster.memory_db.name
  instance_id   = "${local.alloydb_cluster_name}-primary"
  instance_type = "PRIMARY"
  
  machine_config {
    cpu_count = var.alloydb_primary_cpu_count
  }
  
  database_flags = {
    "max_connections" : "1000"
    "shared_buffers" : "8GB"
  }
  
  depends_on = [google_alloydb_cluster.memory_db]
}

# AlloyDB read replicas for high availability
resource "google_alloydb_instance" "replicas" {
  count         = var.alloydb_replica_count
  cluster       = google_alloydb_cluster.memory_db.name
  instance_id   = "${local.alloydb_cluster_name}-replica-${count.index + 1}"
  instance_type = "READ_REPLICA"
  
  machine_config {
    cpu_count = var.alloydb_replica_cpu_count
  }
  
  depends_on = [google_alloydb_instance.primary]
}

# Secret for SuperAGI API key
resource "google_secret_manager_secret" "superagi_api_key" {
  secret_id = "superagi-api-key"
  
  replication {
    auto {
      customer_managed_encryption {
        kms_key_name = var.kms_key
      }
    }
  }
  
  labels = {
    environment = var.environment
    application = "orchestra"
  }
}

# Secret for Gemini API key
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  
  replication {
    auto {
      customer_managed_encryption {
        kms_key_name = var.kms_key
      }
    }
  }
  
  labels = {
    environment = var.environment
    application = "orchestra"
  }
}

# BigQuery dataset for analytics
resource "google_bigquery_dataset" "memory_analytics" {
  dataset_id                  = local.bq_dataset_id
  friendly_name               = "Memory Analytics"
  description                 = "Dataset for Orchestra memory analytics"
  location                    = var.bigquery_location
  delete_contents_on_destroy  = false
  
  labels = {
    environment = var.environment
    application = "orchestra"
  }
}

# BigQuery table for usage metrics
resource "google_bigquery_table" "memory_usage" {
  dataset_id = google_bigquery_dataset.memory_analytics.dataset_id
  table_id   = "memory_usage"
  
  time_partitioning {
    type = "DAY"
    field = "timestamp"
  }
  
  schema = <<EOF
[
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "When the memory operation occurred"
  },
  {
    "name": "operation_type",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Type of memory operation (add, retrieve, etc.)"
  },
  {
    "name": "provider",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Memory provider used (redis, alloydb, etc.)"
  },
  {
    "name": "latency_ms",
    "type": "FLOAT",
    "mode": "REQUIRED",
    "description": "Operation latency in milliseconds"
  },
  {
    "name": "user_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "User ID associated with the memory"
  },
  {
    "name": "session_id",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Session ID if applicable"
  },
  {
    "name": "memory_size_bytes",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Size of memory item in bytes"
  },
  {
    "name": "success",
    "type": "BOOLEAN",
    "mode": "REQUIRED",
    "description": "Whether the operation succeeded"
  }
]
EOF
  
  depends_on = [google_bigquery_dataset.memory_analytics]
}

# Workload identity federation for GitHub Actions
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "${var.prefix}-github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# IAM binding for GitHub Actions
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.integrations_sa.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
  ]
}

# Vertex AI Agent Builder resources
resource "google_storage_bucket" "agent_artifacts" {
  name          = "${var.prefix}-agent-artifacts-${var.project_id}"
  location      = var.region
  force_destroy = false
  
  versioning {
    enabled = true
  }
  
  uniform_bucket_level_access = true
}

# Pub/Sub topic for agent events
resource "google_pubsub_topic" "agent_events" {
  name = "${var.prefix}-agent-events"
}

# Cloud Monitoring alert policies
resource "google_monitoring_alert_policy" "memory_latency" {
  display_name = "Memory System High Latency"
  combiner     = "OR"
  
  conditions {
    display_name = "High latency in memory operations"
    
    condition_threshold {
      filter     = "resource.type = \"redis_instance\" AND resource.labels.instance_id = \"${google_redis_instance.memory_cache.name}\" AND metric.type = \"redis.googleapis.com/stats/latency\""
      duration   = "60s"
      comparison = "COMPARISON_GT"
      threshold_value = 50  # milliseconds
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_PERCENTILE_99"
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  depends_on = [google_redis_instance.memory_cache]
}

# Cost monitoring
resource "google_billing_budget" "memory_budget" {
  billing_account = var.billing_account
  display_name    = "Orchestra Memory System Budget"
  
  budget_filter {
    projects = ["projects/${var.project_id}"]
    labels   = {
      application = "orchestra"
    }
    credit_types_treatment = "EXCLUDE_ALL_CREDITS"
  }
  
  amount {
    specified_amount {
      currency_code = "USD"
      units         = var.monthly_budget
    }
  }
  
  threshold_rules {
    threshold_percent = 0.8
    spend_basis       = "CURRENT_SPEND"
  }
  
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }
  
  all_updates_rule {
    pubsub_topic = google_pubsub_topic.agent_events.id
  }
}
