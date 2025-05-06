/**
 * # Payment Processing Module Outputs
 *
 * Output values for the payment processing infrastructure module
 */

output "project_id" {
  description = "The project ID where payment processing resources are deployed"
  value       = local.project_id
}

output "project_number" {
  description = "The numeric project number"
  value       = local.project_number
}

output "service_account_emails" {
  description = "Map of service account names to their email addresses"
  value       = {
    for k, v in google_service_account.payment_service_accounts : k => v.email
  }
}

output "storage_bucket_names" {
  description = "Map of storage bucket purposes to their names"
  value       = {
    for k, v in google_storage_bucket.payment_data_buckets : k => v.name
  }
}

output "bigquery_dataset_ids" {
  description = "Map of BigQuery dataset names to their fully qualified IDs"
  value       = {
    for k, v in google_bigquery_dataset.payment_datasets : k => v.id
  }
}

output "pubsub_topic" {
  description = "The name of the Pub/Sub topic for payment events"
  value       = google_pubsub_topic.payment_events.name
}

output "pubsub_topic_id" {
  description = "The fully qualified ID of the Pub/Sub topic for payment events"
  value       = google_pubsub_topic.payment_events.id
}

output "function_url" {
  description = "The URL of the deployed payment processor Cloud Function (if enabled)"
  value       = var.deploy_functions ? google_cloudfunctions_function.payment_processor[0].https_trigger_url : null
}

output "vertex_endpoints" {
  description = "Map of Vertex AI endpoint names to their IDs"
  value       = {
    for k, v in google_vertex_ai_endpoint.payment_endpoints : k => v.id
  }
}

output "vector_search_index" {
  description = "The ID of the payment patterns vector search index (if enabled)"
  value       = var.enable_vector_search ? google_vertex_ai_index.payment_vector_search[0].id : null
}

output "cmek_key_id" {
  description = "The ID of the Customer-Managed Encryption Key (if enabled)"
  value       = var.enable_cmek ? google_kms_crypto_key.payment_cmek[0].id : null
}
