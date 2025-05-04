/**
 * Firestore configuration for common environment
 */

# Use the Firestore module for Native mode database
module "firestore" {
  source     = "../../modules/firestore"
  project_id = var.project_id
  database_name = "(default)"
  location = "nam5"
  database_type = "FIRESTORE_NATIVE"
  delete_protection_state = "PROTECTION_DISABLED"
  deletion_policy = "DELETE"
  app_engine_integration_mode = "DISABLED"
}

# Output the database ID for reference
output "firestore_database_id" {
  value       = module.firestore.database_id
  description = "ID of the Firestore database in Native mode"
}
