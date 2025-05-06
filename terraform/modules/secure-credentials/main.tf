/**
 * # Secure Credentials Module
 *
 * This module sets up the secure credential infrastructure for AI Orchestra:
 * - Secret Manager resources
 * - Service accounts with appropriate permissions
 * - Workload Identity Federation configuration
 */

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "service_accounts" {
  description = "Map of service accounts to create with their roles"
  type = map(object({
    display_name = string
    description  = string
    roles        = list(string)
  }))
  default = {
    "vertex-ai-agent" = {
      display_name = "Vertex AI Agent"
      description  = "Service account for Vertex AI operations"
      roles        = ["roles/aiplatform.user", "roles/aiplatform.serviceAgent"]
    },
    "gemini-agent" = {
      display_name = "Gemini Agent"
      description  = "Service account for Gemini API access"
      roles        = ["roles/aiplatform.user"]
    },
    "memory-system" = {
      display_name = "Memory System"
      description  = "Service account for memory system operations"
      roles        = ["roles/firestore.user", "roles/redis.editor"]
    },
    "orchestrator" = {
      display_name = "Orchestrator"
      description  = "Service account for orchestrator operations"
      roles        = ["roles/secretmanager.secretAccessor"]
    },
    "github-actions" = {
      display_name = "GitHub Actions"
      description  = "Service account for GitHub Actions"
      roles        = ["roles/run.admin", "roles/storage.admin", "roles/secretmanager.secretAccessor"]
    }
  }
}

variable "secrets" {
  description = "Map of secrets to create"
  type = map(object({
    secret_data     = string
    replication     = string
    secret_versions = map(string)
  }))
  default = {}
}

# Local variables
locals {
  project_number = data.google_project.project.number
}

# Data sources
data "google_project" "project" {
  project_id = var.project_id
}

# Service accounts
resource "google_service_account" "service_accounts" {
  for_each     = var.service_accounts
  account_id   = each.key
  display_name = each.value.display_name
  description  = each.value.description
  project      = var.project_id
}

# IAM bindings for service accounts
resource "google_project_iam_member" "service_account_roles" {
  for_each = {
    for binding in flatten([
      for sa_key, sa in var.service_accounts : [
        for role in sa.roles : {
          sa_key = sa_key
          role   = role
        }
      ]
    ]) : "${binding.sa_key}-${binding.role}" => binding
  }

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.service_accounts[each.value.sa_key].email}"
}

# Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  provider                  = google-beta
  project                   = var.project_id
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
}

# Workload Identity Provider
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  provider                           = google-beta
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# IAM binding for GitHub Actions to impersonate service account
resource "google_service_account_iam_binding" "github_actions_binding" {
  service_account_id = google_service_account.service_accounts["github-actions"].name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_org}/${var.github_repo}"
  ]
}

# Secret Manager resources
resource "google_secret_manager_secret" "secrets" {
  for_each  = var.secrets
  project   = var.project_id
  secret_id = "${each.key}-${var.env}"
  
  replication {
    auto {
      # Use automatic replication
    }
  }
}

# Secret versions
resource "google_secret_manager_secret_version" "secret_versions" {
  for_each = {
    for version in flatten([
      for secret_key, secret in var.secrets : [
        for version_key, version_data in secret.secret_versions : {
          secret_key   = secret_key
          version_key  = version_key
          version_data = version_data
        }
      ]
    ]) : "${version.secret_key}-${version.version_key}" => version
  }

  secret      = google_secret_manager_secret.secrets["${each.value.secret_key}"].id
  secret_data = each.value.version_data
}

# Service account keys (only created for non-WIF service accounts)
resource "google_service_account_key" "keys" {
  for_each           = { for k, v in var.service_accounts : k => v if k != "github-actions" }
  service_account_id = google_service_account.service_accounts[each.key].name
}

# Store service account keys in Secret Manager
resource "google_secret_manager_secret" "sa_key_secrets" {
  for_each  = { for k, v in var.service_accounts : k => v if k != "github-actions" }
  project   = var.project_id
  secret_id = "${each.key}-key-${var.env}"
  
  replication {
    auto {
      # Use automatic replication
    }
  }
}

resource "google_secret_manager_secret_version" "sa_key_versions" {
  for_each    = { for k, v in var.service_accounts : k => v if k != "github-actions" }
  secret      = google_secret_manager_secret.sa_key_secrets[each.key].id
  secret_data = base64decode(google_service_account_key.keys[each.key].private_key)
}

# Outputs
output "service_account_emails" {
  description = "The emails of the created service accounts"
  value       = { for k, v in google_service_account.service_accounts : k => v.email }
}

output "workload_identity_provider" {
  description = "The Workload Identity Provider resource name"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "secret_names" {
  description = "The names of the created secrets"
  value       = { for k, v in google_secret_manager_secret.secrets : k => v.name }
}

output "service_account_key_secrets" {
  description = "The Secret Manager secrets containing service account keys"
  value       = { for k, v in google_secret_manager_secret.sa_key_secrets : k => v.name }
}