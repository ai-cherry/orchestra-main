/**
 * Pub/Sub resources for Orchestra project
 */

# Topic for Orchestra event notifications
resource "google_pubsub_topic" "orchestra_events" {
  name    = "${local.env_prefix}-events"
  project = var.project_id
  
  labels = local.common_labels
  
  message_retention_duration = "86600s"  # 24 hours + 100 seconds buffer
  
  # Enable message ordering if needed
  message_storage_policy {
    allowed_persistence_regions = [
      var.region
    ]
  }
  
  # Schema for message validation (optional)
  schema_settings {
    schema = google_pubsub_schema.events_schema.id
    encoding = "JSON"
  }
}

# Schema for event messages
resource "google_pubsub_schema" "events_schema" {
  name = "${local.env_prefix}-events-schema"
  project = var.project_id
  type = "AVRO"
  definition = <<EOF
{
  "type": "record",
  "name": "OrchestraEvent",
  "namespace": "com.cherry.ai.orchestra",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "event_type", "type": "string"},
    {"name": "timestamp", "type": "string"},
    {"name": "source", "type": "string"},
    {"name": "payload", "type": ["null", "string"], "default": null}
  ]
}
EOF
}

# Subscription for processing events
resource "google_pubsub_subscription" "events_subscription" {
  name  = "${local.env_prefix}-events-subscription"
  project = var.project_id
  topic = google_pubsub_topic.orchestra_events.name
  
  # Configure message retention
  message_retention_duration = "604800s"  # 7 days
  retain_acked_messages = true
  
  # Configure acknowledgement deadline
  ack_deadline_seconds = 20
  
  # Configure retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"  # 10 minutes
  }
  
  # Enable exactly-once delivery if needed
  enable_exactly_once_delivery = true
  
  # Configure expiration policy
  expiration_policy {
    ttl = "2592000s"  # 30 days
  }
  
  # Configure dead letter policy
  dead_letter_policy {
    dead_letter_topic = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
  
  # Add push configuration if needed
  push_config {
    push_endpoint = "https://${var.region}-${var.project_id}.cloudfunctions.net/process-events"
    
    # Add authentication
    oidc_token {
      service_account_email = google_service_account.orchestra_runner_sa.email
    }
    
    # Add attributes
    attributes = {
      x-goog-version = "v1"
    }
  }
}

# Dead letter topic for failed messages
resource "google_pubsub_topic" "dead_letter" {
  name    = "${local.env_prefix}-events-dead-letter"
  project = var.project_id
  
  labels = merge(local.common_labels, {
    purpose = "dead-letter"
  })
  
  message_retention_duration = "604800s"  # 7 days
}

# Output the topic and subscription IDs for reference
output "pubsub_topic_id" {
  value       = google_pubsub_topic.orchestra_events.id
  description = "ID of the Orchestra Pub/Sub events topic"
}

output "pubsub_subscription_id" {
  value       = google_pubsub_subscription.events_subscription.id
  description = "ID of the Orchestra Pub/Sub events subscription"
}

output "pubsub_dead_letter_topic_id" {
  value       = google_pubsub_topic.dead_letter.id
  description = "ID of the Orchestra Pub/Sub dead letter topic"
}

output "pubsub_schema_id" {
  value       = google_pubsub_schema.events_schema.id
  description = "ID of the Orchestra Pub/Sub events schema"
}
