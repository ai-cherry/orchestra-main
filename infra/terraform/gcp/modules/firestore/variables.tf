variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "database_name" {
  description = "The name of the Firestore database"
  type        = string
  default     = "(default)"
}

variable "location" {
  description = "The location of the Firestore database"
  type        = string
  default     = "us-central1"
}

variable "database_type" {
  description = "The type of Firestore database (FIRESTORE_NATIVE or DATASTORE_MODE)"
  type        = string
  default     = "FIRESTORE_NATIVE"
}

variable "delete_protection_state" {
  description = "The delete protection state of the database (PROTECTION_ENABLED or PROTECTION_DISABLED)"
  type        = string
  default     = "PROTECTION_DISABLED"
}

variable "deletion_policy" {
  description = "The deletion policy for the database (DELETE or ABANDON)"
  type        = string
  default     = "DELETE"
}

variable "app_engine_integration_mode" {
  description = "The App Engine integration mode (ENABLED or DISABLED)"
  type        = string
  default     = "DISABLED"
}
