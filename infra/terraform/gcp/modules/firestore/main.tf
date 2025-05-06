# Basic Firestore module

resource "google_firestore_database" "database" {
  project                     = var.project_id
  name                        = var.database_name
  location_id                 = var.location
  type                        = var.database_type
  delete_protection_state     = var.delete_protection_state
  deletion_policy             = var.deletion_policy
  app_engine_integration_mode = var.app_engine_integration_mode
}
