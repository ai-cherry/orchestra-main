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
  
  # Note: point-in-time recovery and concurrency mode are not supported by the current module
  # These features would need to be added to the module or configured directly
}

# Create a backup schedule for the Firestore database
# Commented out due to compatibility issues with current provider version
# Will need to be updated with correct resource definition
/*
resource "google_firestore_backup_schedule" "daily_backup" {
  project = var.project_id
  database = "(default)"
  
  # Configuration will need to be updated based on provider documentation
  # retention = 7  # Keep last 7 daily backups
  
  # schedule = "every day 00:00"  # Daily at midnight
  
  # id = "${local.env_prefix}-daily-backup"
}
*/

# Output moved to outputs.tf
