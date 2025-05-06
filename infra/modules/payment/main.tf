/**
 * # GCP Payment Processing Infrastructure Module
 *
 * This Terraform module creates a secure infrastructure for payment data processing
 * and analysis in Google Cloud Platform with focus on security and isolation.
 */

# ------------ Project Setup --------------
resource "google_project" "payment_project" {
  count           = var.create_project ? 1 : 0
  name            = "Payment Processing ${title(var.env)}"
  project_id      = var.project_id
  billing_account = var.billing_account
  
  labels = {
    environment = var.env
    purpose     = "payment-processing"
    managed_by  = "terraform"
  }
}

# ------------ Service Accounts --------------
resource "google_service_account" "payment_service_accounts" {
  for_each     = var.service_accounts
  
  project      = local.project_id
  account_id   = "${each.key}-${var.env}"
  display_name = "Payment ${title(replace(each.key, "-", " "))} (${var.env})"
  description  = "Service account for ${each.key} in the payment processing system"
}

# Assign IAM roles to the service accounts
resource "google_project_iam_member" "payment_sa_roles" {
  for_each = local.flattened_sa_roles
  
  project = local.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.payment_service_accounts[each.value.sa_key].email}"
}

# ------------ Storage Infrastructure --------------

# Cloud Storage buckets for payment data with CMEK
resource "google_storage_bucket" "payment_data_buckets" {
  for_each = var.storage_buckets
  
  name          = "${var.project_id}-${each.key}-${var.env}"
  location      = lookup(each.value, "location", var.region)
  storage_class = lookup(each.value, "storage_class", "STANDARD")
  project       = local.project_id
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = lookup(each.value, "versioning_enabled", true)
  }
  
  lifecycle_rule {
    condition {
      age = lookup(each.value, "retention_days", 90)
    }
    action {
      type = "Delete"
    }
  }
  
  dynamic "encryption" {
    for_each = var.enable_cmek ? [1] : []
    content {
      default_kms_key_name = google_kms_crypto_key.payment_cmek[0].id
    }
  }
}

# BigQuery datasets for payment data
resource "google_bigquery_dataset" "payment_datasets" {
  for_each = var.bigquery_datasets
  
  dataset_id                  = each.key
  friendly_name               = title(replace(each.key, "_", " "))
  description                 = lookup(each.value, "description", "Payment processing dataset for ${each.key}")
  location                    = lookup(each.value, "location", var.region)
  default_table_expiration_ms = lookup(each.value, "expiration_ms", null)
  project                     = local.project_id
  
  delete_contents_on_destroy = lookup(each.value, "delete_contents_on_destroy", false)
  
  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }
  
  dynamic "access" {
    for_each = contains(lookup(var.service_accounts["payment-data-reader"], "roles", []), "roles/bigquery.dataViewer") ? [1] : []
    content {
      role           = "READER"
      user_by_email  = google_service_account.payment_service_accounts["payment-data-reader"].email
    }
  }
  
  dynamic "access" {
    for_each = contains(lookup(var.service_accounts["payment-reporting"], "roles", []), "roles/bigquery.dataViewer") ? [1] : []
    content {
      role           = "READER"
      user_by_email  = google_service_account.payment_service_accounts["payment-reporting"].email
    }
  }
  
  dynamic "access" {
    for_each = contains(lookup(var.service_accounts["payment-data-processor"], "roles", []), "roles/bigquery.dataEditor") ? [1] : []
    content {
      role           = "WRITER"
      user_by_email  = google_service_account.payment_service_accounts["payment-data-processor"].email
    }
  }
}

# Firestore collections (represented through IAM since collections are created at runtime)
resource "google_project_iam_binding" "firestore_collections" {
  project = local.project_id
  role    = "roles/datastore.user"
  
  members = [
    "serviceAccount:${google_service_account.payment_service_accounts["payment-data-processor"].email}",
    "serviceAccount:${google_service_account.payment_service_accounts["payment-data-reader"].email}"
  ]
}

# ------------ Vertex AI --------------

# Vertex AI Endpoints for payment analysis
resource "google_vertex_ai_endpoint" "payment_endpoints" {
  for_each     = var.vertex_endpoints
  
  display_name = "${each.key}-${var.env}"
  description  = lookup(each.value, "description", "Payment analysis endpoint for ${each.key}")
  location     = lookup(each.value, "location", var.region)
  project      = local.project_id
}

# Vector Search Index for payment patterns
resource "google_vertex_ai_index" "payment_vector_search" {
  count = var.enable_vector_search ? 1 : 0
  
  display_name   = "payment-patterns-${var.env}"
  description    = "Vector search index for payment patterns analysis"
  project        = local.project_id
  region         = var.region
  
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.payment_data_buckets["embeddings"].name}/vectors"
    config {
      dimensions = var.vector_dimension
      approximate_neighbors_count = 150
      distance_measure_type = "DOT_PRODUCT_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }
  
  index_update_method = "BATCH_UPDATE"
}

# ------------ Security Controls --------------

# KMS for customer-managed encryption keys (CMEK)
resource "google_kms_key_ring" "payment_keyring" {
  count = var.enable_cmek ? 1 : 0
  
  name     = "payment-keyring-${var.env}"
  location = var.region
  project  = local.project_id
}

resource "google_kms_crypto_key" "payment_cmek" {
  count = var.enable_cmek ? 1 : 0
  
  name            = "payment-cmek-${var.env}"
  key_ring        = google_kms_key_ring.payment_keyring[0].id
  rotation_period = "7776000s" # 90 days
  
  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "SOFTWARE"
  }
}

# Grant service accounts access to the KMS key
resource "google_kms_crypto_key_iam_binding" "crypto_key_binding" {
  count = var.enable_cmek ? 1 : 0
  
  crypto_key_id = google_kms_crypto_key.payment_cmek[0].id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  
  members = [
    for sa_key in keys(var.service_accounts) :
    "serviceAccount:${google_service_account.payment_service_accounts[sa_key].email}"
  ]
}

# VPC Service Controls (if enabled)
resource "google_access_context_manager_service_perimeter" "payment_perimeter" {
  count = var.enable_vpc_sc ? 1 : 0
  
  name         = "accessPolicies/${var.access_policy_id}/servicePerimeters/payment_processing_${var.env}"
  title        = "Payment Processing ${title(var.env)}"
  perimeter_type = "PERIMETER_TYPE_REGULAR"
  
  status {
    restricted_services = [
      "bigquery.googleapis.com",
      "storage.googleapis.com",
      "aiplatform.googleapis.com", 
      "datastore.googleapis.com"
    ]
    
    resources = [
      "projects/${local.project_number}"
    ]
    
    # Ingress/egress policies would be defined here for specific access patterns
  }
}

# ------------ Audit Logging --------------

# Enable Data Access audit logs
resource "google_project_iam_audit_config" "payment_data_access_logs" {
  project = local.project_id
  service = "allServices"
  
  audit_log_config {
    log_type = "DATA_READ"
  }
  
  audit_log_config {
    log_type = "DATA_WRITE"
  }
  
  audit_log_config {
    log_type = "ADMIN_READ"
  }
}

# Log sink for long-term storage of audit logs
resource "google_logging_project_sink" "payment_audit_sink" {
  count = var.audit_log_retention_days > 0 ? 1 : 0
  
  name        = "payment-audit-sink-${var.env}"
  destination = "storage.googleapis.com/${google_storage_bucket.payment_data_buckets["audit-logs"].name}"
  
  # Use a filter that includes payment processing operations
  filter      = "resource.type=((\"bigquery_resource\" AND resource.labels.dataset_id=\"payment\") OR \"cloudfunction\" OR \"datastore_database\")"
  
  project = local.project_id
  
  unique_writer_identity = true
}

resource "google_storage_bucket_iam_binding" "audit_sink_storage_binding" {
  count  = var.audit_log_retention_days > 0 ? 1 : 0
  bucket = google_storage_bucket.payment_data_buckets["audit-logs"].name
  role   = "roles/storage.objectCreator"
  
  members = [
    google_logging_project_sink.payment_audit_sink[0].writer_identity,
  ]
}

# ------------ Pub/Sub for Payment Events --------------

resource "google_pubsub_topic" "payment_events" {
  name    = "payment-events-${var.env}"
  project = local.project_id
  
  message_storage_policy {
    allowed_persistence_regions = [
      var.region
    ]
  }
  
  dynamic "schema_settings" {
    for_each = var.enable_pubsub_schemas ? [1] : []
    content {
      schema = google_pubsub_schema.payment_event_schema[0].id
      encoding = "JSON"
    }
  }
}

resource "google_pubsub_schema" "payment_event_schema" {
  count = var.enable_pubsub_schemas ? 1 : 0
  
  name       = "payment-events-schema-${var.env}"
  type       = "AVRO"
  definition = <<EOF
{
  "type": "record",
  "name": "PaymentEvent",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "event_type", "type": "string"},
    {"name": "timestamp", "type": "string"},
    {"name": "user_id", "type": "string"},
    {"name": "amount", "type": "double"},
    {"name": "currency", "type": "string"},
    {"name": "status", "type": "string"},
    {"name": "metadata", "type": {"type": "map", "values": "string"}}
  ]
}
EOF
  project = local.project_id
}

# ------------ Cloud Functions for Data Processing --------------

resource "google_storage_bucket" "function_code_bucket" {
  name          = "${var.project_id}-functions-${var.env}"
  location      = var.region
  force_destroy = true
  project       = local.project_id
}

resource "google_cloudfunctions_function" "payment_processor" {
  count = var.deploy_functions ? 1 : 0
  
  name        = "payment-processor-${var.env}"
  description = "Function to process payment events"
  runtime     = "python310"
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_code_bucket.name
  source_archive_object = google_storage_bucket_object.function_archive[0].name
  entry_point           = "process_payment"
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.payment_events.name
  }
  
  service_account_email = google_service_account.payment_service_accounts["payment-data-processor"].email
  project               = local.project_id
  region                = var.region
  
  environment_variables = {
    ENVIRONMENT = var.env
    BQ_DATASET = "payment_processed"
    FIRESTORE_COLLECTION = "payments"
  }
}

resource "google_storage_bucket_object" "function_archive" {
  count  = var.deploy_functions ? 1 : 0
  name   = "function-source.zip"
  bucket = google_storage_bucket.function_code_bucket.name
  source = var.function_source_zip_path != "" ? var.function_source_zip_path : null
  
  content = var.function_source_zip_path == "" ? "# Placeholder for function code" : null
}

# ------------ Locals --------------

locals {
  # Use existing project if not creating a new one
  project_id = var.create_project ? google_project.payment_project[0].project_id : var.project_id
  
  # Get project number - required for VPC SC
  project_number = var.create_project ? google_project.payment_project[0].number : data.google_project.existing_project[0].number
  
  # Flatten the service account roles for easier resource creation
  flattened_sa_roles = flatten([
    for sa_key, sa_config in var.service_accounts : [
      for role in lookup(sa_config, "roles", []) : {
        sa_key = sa_key
        role   = role
      }
    ]
  ])
}

# ------------ Data Sources --------------

data "google_project" "existing_project" {
  count      = var.create_project ? 0 : 1
  project_id = var.project_id
}
