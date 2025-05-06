variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

# Firestore Database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"  # Using the default database
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  
  # Add environment-specific point-in-time recovery settings
  point_in_time_recovery_enablement = var.env == "prod" ? "POINT_IN_TIME_RECOVERY_ENABLED" : "POINT_IN_TIME_RECOVERY_DISABLED"
  
  # Disable delete protection in dev/stage environments, enable in prod
  delete_protection_state = var.env == "prod" ? "DELETE_PROTECTION_ENABLED" : "DELETE_PROTECTION_DISABLED"
}

# Add Firestore collection and index for persona management
resource "google_firestore_index" "persona_index" {
  collection = "personas-${var.env}"
  database   = google_firestore_database.database.name
  
  fields {
    field_path = "name"
    order      = "ASCENDING"
  }
  
  fields {
    field_path = "updated_at"
    order      = "DESCENDING"
  }
}

# Add Firestore collection and index for conversation history
resource "google_firestore_index" "conversation_index" {
  collection = "conversations-${var.env}"
  database   = google_firestore_database.database.name
  
  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }
  
  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }
}

# Add Firestore collection and index for memory items
resource "google_firestore_index" "memory_index" {
  collection = "memory-${var.env}"
  database   = google_firestore_database.database.name
  
  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }
  
  fields {
    field_path = "item_type"
    order      = "ASCENDING"
  }
  
  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }
}

output "database_id" {
  value = google_firestore_database.database.name
}
