variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

variable "portkey_api_key_name" {
  description = "Name for the Portkey API key secret"
  type        = string
  default     = "portkey-api-key"
}

variable "openrouter_api_key_name" {
  description = "Name for the OpenRouter API key secret"
  type        = string
  default     = "openrouter"
}

variable "secret_accessors" {
  description = "Map of service account emails to secrets they need access to"
  type        = map(list(string))
  default     = {}
}

# Enable Secret Manager API
resource "google_project_service" "secretmanager_api" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Create Portkey API Key Secret
resource "google_secret_manager_secret" "portkey_api_key" {
  project   = var.project_id
  secret_id = "${var.portkey_api_key_name}-${var.env}"
  
  replication {
    automatic = true
  }
  
  labels = {
    environment = var.env
    purpose     = "llm-integration"
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# Create OpenRouter API Key Secret
resource "google_secret_manager_secret" "openrouter_api_key" {
  project   = var.project_id
  secret_id = "${var.openrouter_api_key_name}-${var.env}"
  
  replication {
    automatic = true
  }
  
  labels = {
    environment = var.env
    purpose     = "llm-integration"
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# Create a secret for storing Vertex AI API key
resource "google_secret_manager_secret" "vertex_api_key" {
  project   = var.project_id
  secret_id = "vertex-api-key-${var.env}"
  
  replication {
    automatic = true
  }
  
  labels = {
    environment = var.env
    purpose     = "vertex-integration"
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# Create a secret for storing external API keys (e.g. for agents)
resource "google_secret_manager_secret" "external_apis" {
  project   = var.project_id
  secret_id = "external-apis-${var.env}"
  
  replication {
    automatic = true
  }
  
  labels = {
    environment = var.env
    purpose     = "external-integrations"
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# Create a secret for storing service account keys (temporary, for dev/test only)
resource "google_secret_manager_secret" "service_account_keys" {
  count      = var.env == "prod" ? 0 : 1
  project    = var.project_id
  secret_id  = "service-account-keys-${var.env}"
  
  replication {
    automatic = true
  }
  
  labels = {
    environment = var.env
    purpose     = "development"
    temporary   = "true"
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# Configure access for each service account to its required secrets
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

output "portkey_api_key_secret" {
  value       = google_secret_manager_secret.portkey_api_key.id
  description = "The ID of the Portkey API key secret"
}

output "openrouter_api_key_secret" {
  value       = google_secret_manager_secret.openrouter_api_key.id
  description = "The ID of the OpenRouter API key secret"
}

output "vertex_api_key_secret" {
  value       = google_secret_manager_secret.vertex_api_key.id
  description = "The ID of the Vertex AI API key secret"
}

output "external_apis_secret" {
  value       = google_secret_manager_secret.external_apis.id
  description = "The ID of the external APIs secret"
}
