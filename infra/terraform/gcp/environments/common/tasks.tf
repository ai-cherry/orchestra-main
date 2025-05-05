/**
 * Cloud Tasks resources for Orchestra project
 */

# Cloud Tasks Queue for Orchestra background tasks
resource "google_cloud_tasks_queue" "orchestra_tasks_queue" {
  name     = "orchestra-tasks-queue"
  project  = var.project_id
  location = var.region
  
  rate_limits {
    max_concurrent_dispatches = 10
    max_dispatches_per_second = 20
  }
  
  retry_config {
    max_attempts = 5
    min_backoff  = "1s"
    max_backoff  = "60s"
    max_retry_duration = "4h"
    max_doublings = 3
  }
}

# Output the queue ID for reference
output "tasks_queue_id" {
  value       = google_cloud_tasks_queue.orchestra_tasks_queue.id
  description = "ID of the Orchestra Cloud Tasks queue"
}
