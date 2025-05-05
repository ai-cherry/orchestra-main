/**
 * Pub/Sub resources for Orchestra project
 */

# Topic for Orchestra event notifications
resource "google_pubsub_topic" "orchestra_events" {
  name    = "orchestra-events"
  project = var.project_id
  
  labels = {
    environment = "common"
    managed-by  = "terraform"
  }
  
  message_retention_duration = "86600s"  # 24 hours + 100 seconds buffer
}

# Output the topic ID for reference
output "pubsub_topic_id" {
  value       = google_pubsub_topic.orchestra_events.id
  description = "ID of the Orchestra Pub/Sub events topic"
}
