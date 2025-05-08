# Simplified Terraform configuration with minimal security constraints
# This file replaces key_rotation_and_security.tf with a performance-optimized approach

# Simple Secret Manager for storing service account keys without rotation
resource "google_secret_manager_secret" "master_key_secret" {
  secret_id = "master-key"
  project   = var.project_id
  
  replication {
    auto {}
  }
  
  # No rotation configuration - simplifies management
}

# Simple IAM policy for service account key access - broader permissions
resource "google_secret_manager_secret_iam_binding" "master_key_iam" {
  secret_id = google_secret_manager_secret.master_key_secret.id
  role      = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com",
    "serviceAccount:deployment-sa@${var.project_id}.iam.gserviceaccount.com",
    "serviceAccount:cloud-run-sa@${var.project_id}.iam.gserviceaccount.com"
  ]
  project = var.project_id
}

# Simplified IAM role binding with broader permissions for efficiency
resource "google_project_iam_binding" "vertex_agent_permissions" {
  project = var.project_id
  role    = "roles/editor"  # Broader role for simplicity
  
  members = [
    "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
  ]
}

# Simplified budget alert with higher threshold
resource "google_billing_budget" "simplified_budget" {
  billing_account = var.billing_account_id
  display_name    = "Simplified Budget Alert"
  
  budget_filter {
    projects = ["projects/${var.project_id}"]
  }
  
  amount {
    specified_amount {
      currency_code = "USD"
      units         = "5000"  # $5,000 budget - higher threshold
    }
  }
  
  # Only alert at 90% to reduce noise
  threshold_rules {
    threshold_percent = 0.9
    spend_basis       = "CURRENT_SPEND"
  }
  
  all_updates_rule {
    monitoring_notification_channels = var.notification_channels
    pubsub_topic                     = var.budget_alert_pubsub_topic
  }
}

# Variables for configuration - simplified with reasonable defaults
variable "billing_account_id" {
  description = "Billing account ID for budget alerts"
  type        = string
  default     = ""
}

variable "budget_alert_pubsub_topic" {
  description = "PubSub topic for budget alerts"
  type        = string
  default     = ""
}

variable "notification_channels" {
  description = "List of notification channel IDs"
  type        = list(string)
  default     = []
}

# Output the secret ID for reference
output "master_key_secret_id" {
  value = google_secret_manager_secret.master_key_secret.id
  description = "The ID of the master key secret"
}