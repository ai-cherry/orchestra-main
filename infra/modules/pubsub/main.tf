variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

# Create the main Pub/Sub topic for the event bus
resource "google_pubsub_topic" "event_bus" {
  name         = "orchestra-bus-${var.env}"
  project      = var.project_id
  labels = {
    environment = var.env
  }
  
  # Enable message ordering for sequential processing
  message_retention_duration = "86600s"  # 24 hours and 10 minutes
  
  # Set a reasonable message size limit
  message_storage_policy {
    allowed_persistence_regions = [
      "us-west2",  # Match with the primary region
    ]
  }
}

# Create a dead-letter topic for handling failures
resource "google_pubsub_topic" "dead_letter" {
  name         = "orchestra-bus-${var.env}-dead-letter"
  project      = var.project_id
  labels = {
    environment = var.env
    type        = "dead-letter"
  }
  
  # Keep failed messages longer
  message_retention_duration = "604800s"  # 7 days
}

# Create a default subscription for processing events
resource "google_pubsub_subscription" "default" {
  name    = "orchestra-bus-${var.env}-default"
  topic   = google_pubsub_topic.event_bus.name
  project = var.project_id
  
  # Configure delivery with retries and dead-letter
  ack_deadline_seconds = 60  # Longer deadline for processing
  
  message_retention_duration = "604800s"  # 7 days retention
  retain_acked_messages      = false
  
  expiration_policy {
    ttl = ""  # Never expire
  }
  
  # Retry and dead-letter configuration
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"  # 10 minutes max backoff
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

# Create a high-priority subscription for critical events
resource "google_pubsub_subscription" "high_priority" {
  name    = "orchestra-bus-${var.env}-high-priority"
  topic   = google_pubsub_topic.event_bus.name
  project = var.project_id
  
  # Configure for higher throughput and lower latency
  ack_deadline_seconds = 30
  
  # Shorter retention for high-priority messages
  message_retention_duration = "86400s"  # 1 day
  retain_acked_messages      = false
  
  expiration_policy {
    ttl = ""  # Never expire
  }
  
  # More aggressive retry policy
  retry_policy {
    minimum_backoff = "5s"
    maximum_backoff = "60s"  # 1 minute max backoff
  }
  
  # Still use dead-letter for failures
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 3  # Fewer attempts before dead-letter
  }
  
  # Filter for high-priority messages
  filter = "attributes.priority = \"high\""
}

# Create a subscription for handling dead-letter messages
resource "google_pubsub_subscription" "dead_letter_subscription" {
  name    = "orchestra-bus-${var.env}-dead-letter-sub"
  topic   = google_pubsub_topic.dead_letter.name
  project = var.project_id
  
  # Long retention for investigation
  message_retention_duration = "1209600s"  # 14 days
  retain_acked_messages      = true
  
  expiration_policy {
    ttl = ""  # Never expire
  }
  
  # No retry or dead-letter for the dead-letter subscription
}

output "topic_id" {
  value = google_pubsub_topic.event_bus.id
}

output "dead_letter_topic_id" {
  value = google_pubsub_topic.dead_letter.id
}

output "default_subscription_id" {
  value = google_pubsub_subscription.default.id
}

output "high_priority_subscription_id" {
  value = google_pubsub_subscription.high_priority.id
}
