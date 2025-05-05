/**
 * Firestore configuration for common environment
 */

# Use the Firestore module for Native mode database
module "firestore" {
  source     = "../../modules/firestore"
  project_id = var.project_id
  database_name = "(default)"
  location = var.firestore_location
  database_type = "FIRESTORE_NATIVE"
  delete_protection_state = var.enable_deletion_protection ? "PROTECTION_ENABLED" : "PROTECTION_DISABLED"
  deletion_policy = var.enable_deletion_protection ? "ABANDON" : "DELETE"
  app_engine_integration_mode = "DISABLED"
  
  # Add point-in-time recovery for data protection
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"
  
  # Add concurrency mode for better performance
  concurrency_mode = "OPTIMISTIC"
}

# Create a backup schedule for the Firestore database
resource "google_firestore_backup_schedule" "daily_backup" {
  project = var.project_id
  location = var.firestore_location
  
  retention {
    backup_retention_count = 7  # Keep last 7 daily backups
  }
  
  recurrence = "every day 00:00"  # Daily at midnight
  
  backup_schedule_id = "${local.env_prefix}-daily-backup"
}

# Output the database ID for reference
output "firestore_database_id" {
  value       = module.firestore.database_id
  description = "ID of the Firestore database in Native mode"
}
