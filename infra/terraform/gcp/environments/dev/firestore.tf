/**
 * Firestore configuration for dev environment
 */

# Use the Firestore module for Native mode database
module "firestore" {
  source     = "../../../modules/firestore"
  project_id = var.project_id
  region     = var.region
  env        = var.env
}

# Output the database ID for reference
output "firestore_database_id" {
  value       = module.firestore.database_id
  description = "ID of the Firestore database in Native mode"
}
