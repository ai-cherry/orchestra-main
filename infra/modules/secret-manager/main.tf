variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

variable "region" {
  description = "GCP Region for secret replication"
  type        = string
  default     = "us-central1"
}

variable "secret_accessors" {
  description = "Map of service account emails to secrets they need access to"
  type        = map(list(string))
  default     = {}
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.63.0"
    }
  }
}

# Enable Secret Manager API
resource "google_project_service" "secretmanager_api" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Configure additional access for service accounts provided via variables
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each = {
    for pair in flatten([
      for sa_email, secret_list in var.secret_accessors : [
        for secret in secret_list : {
          sa_email = sa_email
          secret   = secret
        }
      ]
    ]) : "${pair.sa_email}-${pair.secret}" => pair
  }
  
  project      = var.project_id
  secret_id    = each.value.secret
  role         = "roles/secretmanager.secretAccessor"
  member       = "serviceAccount:${each.value.sa_email}"
}
