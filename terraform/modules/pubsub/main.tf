# PubSub Module for AI Orchestra
# Provides PubSub topics and subscriptions for agent communication

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-west4"
}

variable "environment" {
  description = "Deployment environment (prod, staging, dev)"
  type        = string
  default     = "dev"
}

variable "service_account_email" {
  description = "Service account email for PubSub authentication"
  type        = string
}

variable "topics" {
  description = "Map of PubSub topics to create with their configurations"
  type = map(object({
    labels       = optional(map(string), {})
    message_retention_duration = optional(string, "86600s") # Default 24 hours
  }))
  default = {
    "agent-events" = {
      labels = {
        purpose = "agent-communication"
      }
    },
    "agent-tasks" = {
      labels = {
        purpose = "task-distribution"
      }
    },
    "agent-results" = {
      labels = {
        purpose = "task-results"
      }
    }
  }
}

variable "subscriptions" {
  description = "Map of PubSub subscriptions to create with their configurations"
  type = map(object({
    topic               = string
    labels              = optional(map(string), {})
    ack_deadline_seconds = optional(number, 20)
    message_retention_duration = optional(string, "604800s") # Default 7 days
    retain_acked_messages = optional(bool, false)
    enable_message_ordering = optional(bool, false)
    expiration_policy_ttl = optional(string, null)
    filter              = optional(string, null)
    dead_letter_topic   = optional(string, null)
    max_delivery_attempts = optional(number, 5)
    minimum_backoff     = optional(string, "10s")
    maximum_backoff     = optional(string, "600s") # 10 minutes
  }))
  default = {
    "agent-events-sub" = {
      topic = "agent-events"
      labels = {
        purpose = "agent-communication"
      }
      enable_message_ordering = true
    },
    "agent-tasks-sub" = {
      topic = "agent-tasks"
      labels = {
        purpose = "task-distribution"
      }
    },
    "agent-results-sub" = {
      topic = "agent-results"
      labels = {
        purpose = "task-results"
      }
    }
  }
}

# Create PubSub topics
resource "google_pubsub_topic" "topics" {
  for_each = var.topics
  
  name    = "${each.key}-${var.environment}"
  project = var.project_id
  
  message_retention_duration = each.value.message_retention_duration
  
  labels = merge(
    each.value.labels,
    {
      environment = var.environment
      managed_by  = "terraform"
    }
  )
}

# Create PubSub subscriptions
resource "google_pubsub_subscription" "subscriptions" {
  for_each = var.subscriptions
  
  name    = "${each.key}-${var.environment}"
  topic   = google_pubsub_topic.topics[each.value.topic].name
  project = var.project_id
  
  labels = merge(
    each.value.labels,
    {
      environment = var.environment
      managed_by  = "terraform"
    }
  )
  
  ack_deadline_seconds = each.value.ack_deadline_seconds
  message_retention_duration = each.value.message_retention_duration
  retain_acked_messages = each.value.retain_acked_messages
  enable_message_ordering = each.value.enable_message_ordering
  filter = each.value.filter
  
  dynamic "expiration_policy" {
    for_each = each.value.expiration_policy_ttl != null ? [1] : []
    content {
      ttl = each.value.expiration_policy_ttl
    }
  }
  
  dynamic "dead_letter_policy" {
    for_each = each.value.dead_letter_topic != null ? [1] : []
    content {
      dead_letter_topic     = google_pubsub_topic.topics[each.value.dead_letter_topic].id
      max_delivery_attempts = each.value.max_delivery_attempts
    }
  }
  
  retry_policy {
    minimum_backoff = each.value.minimum_backoff
    maximum_backoff = each.value.maximum_backoff
  }
}

# Grant publish permissions to the service account
resource "google_pubsub_topic_iam_member" "publisher" {
  for_each = google_pubsub_topic.topics
  
  project = var.project_id
  topic   = each.value.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.service_account_email}"
}

# Grant subscribe permissions to the service account
resource "google_pubsub_subscription_iam_member" "subscriber" {
  for_each = google_pubsub_subscription.subscriptions
  
  project      = var.project_id
  subscription = each.value.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${var.service_account_email}"
}

# Outputs
output "topic_names" {
  description = "The names of the created PubSub topics"
  value = {
    for k, v in google_pubsub_topic.topics : k => v.name
  }
}

output "subscription_names" {
  description = "The names of the created PubSub subscriptions"
  value = {
    for k, v in google_pubsub_subscription.subscriptions : k => v.name
  }
}