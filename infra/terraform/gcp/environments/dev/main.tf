terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

locals {
  env      = var.env
  location = var.region
  labels = {
    environment = local.env
    managed-by  = "terraform"
    project     = "orchestra"
  }
}

# Reference the service account created in service_accounts.tf
resource "google_service_account" "orchestrator_sa" {
  account_id   = "orchestrator-${local.env}-sa"
  display_name = "Orchestrator Service Account for ${local.env}"
  description  = "Service account for the Orchestra application in ${local.env} environment"
}

resource "google_project_iam_member" "orchestrator_sa_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/firestore.user",
    "roles/aiplatform.user",
    "roles/storage.objectUser",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# Secret management
resource "google_secret_manager_secret" "orchestrator_secrets" {
  for_each = {
    "openai-api-key"     = "OpenAI API Key"
    "anthropic-api-key"  = "Anthropic API Key"
    "gemini-api-key"     = "Google Gemini API Key"
    "redis-password"     = "Redis Password"
    "database-password"  = "Database Password"
  }
  
  secret_id = "orchestrator-${local.env}-${each.key}"
  
  replication {
    auto {
      customer_managed_encryption {
        kms_key_name = "projects/${var.project_id}/locations/global/keyRings/orchestrator-${local.env}-kr/cryptoKeys/orchestrator-${local.env}-key"
      }
    }
  }
  
  labels = merge(local.labels, {
    purpose = "orchestra-credentials"
  })
}

# Create empty versions of the secrets (values will be populated manually)
resource "google_secret_manager_secret_version" "orchestrator_secret_versions" {
  for_each = google_secret_manager_secret.orchestrator_secrets
  
  secret      = each.value.id
  secret_data = "placeholder-replace-me"
}

# Create secret for OpenRouter API (fixes the "automatic" argument issue)
resource "google_secret_manager_secret" "openrouter" {
  secret_id = "orchestrator-${local.env}-openrouter"
  
  replication {
    auto {
      customer_managed_encryption {
        kms_key_name = "projects/${var.project_id}/locations/global/keyRings/orchestrator-${local.env}-kr/cryptoKeys/orchestrator-${local.env}-key"
      }
    }
  }
  
  labels = merge(local.labels, {
    purpose = "third-party-api-key"
  })
}

# Create Cloud Storage buckets
resource "google_storage_bucket" "orchestrator_storage" {
  name          = "orchestrator-${local.env}-storage-${var.project_id}"
  location      = var.region
  storage_class = "STANDARD"
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
  
  labels = local.labels
  
  uniform_bucket_level_access = true
}

# Firestore database (if not already created)
resource "google_app_engine_application" "app" {
  count = var.create_firestore_database ? 1 : 0
  
  project     = var.project_id
  location_id = var.firestore_location
  database_type = "CLOUD_FIRESTORE"
}