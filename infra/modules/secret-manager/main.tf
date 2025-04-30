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

variable "portkey_api_key_name" {
  description = "Name for the Portkey API key secret"
  type        = string
  default     = "portkey-api-key"
}

variable "openrouter_api_key_name" {
  description = "Name for the OpenRouter API key secret"
  type        = string
  default     = "openrouter-api-key"
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

# LLM Provider Secrets
# Using for_each to create multiple similar secrets efficiently
resource "google_secret_manager_secret" "llm_api_keys" {
  for_each = {
    "anthropic-api-key"     = "Anthropic API key for Claude models"
    "openai-api-key"        = "OpenAI API key for GPT models"
    "google-api-key"        = "Google API key for Gemini models"
    "openrouter-api-key"    = "OpenRouter API key for multi-model access"
    "mistral-api-key"       = "Mistral AI API key"
    "together-ai-api-key"   = "Together.ai API key"
    "deepseek-api-key"      = "DeepSeek AI API key"
    "perplexity-api-key"    = "Perplexity AI API key"
    "cohere-api-key"        = "Cohere API key"
    "huggingface-api-token" = "HuggingFace API token"
  }

  project   = var.project_id
  secret_id = "${each.key}-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = {
    environment = var.env
    purpose     = "llm-integration"
    category    = "llm-api-keys"
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# Tool API Keys
resource "google_secret_manager_secret" "tool_api_keys" {
  for_each = {
    "portkey-api-key"        = "Portkey API key for LLM routing"
    "vertex-api-key"         = "Vertex AI API key"
    "apify-api-token"        = "Apify API token for web scraping"
    "apollo-io-api-key"      = "Apollo.io API key"
    "brave-api-key"          = "Brave Search API key"
    "exa-api-key"            = "Exa API key" 
    "tavily-api-key"         = "Tavily API key for search"
    "eleven-labs-api-key"    = "ElevenLabs API key for voice synthesis"
  }

  project   = var.project_id
  secret_id = "${each.key}-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = {
    environment = var.env
    purpose     = "tool-integration"
    category    = "tool-api-keys"
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# Infrastructure Secrets
resource "google_secret_manager_secret" "infrastructure_secrets" {
  for_each = {
    "redis-auth"           = "Redis authentication credentials"
    "db-credentials"       = "Database credentials"
    "external-apis"        = "External API configuration"
  }

  project   = var.project_id
  secret_id = "${each.key}-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = {
    environment = var.env
    purpose     = "infrastructure"
    category    = "infrastructure-secrets"
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# GCP Secrets
resource "google_secret_manager_secret" "gcp_secrets" {
  for_each = var.env != "prod" ? {
    "service-account-keys" = "Service account keys (non-prod only)"
    "gcp-client-secret"    = "GCP OAuth client secret"
    "gcp-service-account-key" = "GCP service account key"
  } : {
    "gcp-client-secret"    = "GCP OAuth client secret"
    "gcp-service-account-key" = "GCP service account key"
  }

  project   = var.project_id
  secret_id = "${each.key}-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = {
    environment = var.env
    purpose     = "gcp-configuration"
    category    = "gcp-secrets"
    temporary   = each.key == "service-account-keys" ? "true" : "false"
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

# Output organized by category for easier consumption
output "llm_api_key_secrets" {
  value       = {
    for key, secret in google_secret_manager_secret.llm_api_keys :
    key => secret.id
  }
  description = "The IDs of LLM API key secrets"
}

output "tool_api_key_secrets" {
  value       = {
    for key, secret in google_secret_manager_secret.tool_api_keys :
    key => secret.id
  }
  description = "The IDs of tool integration API key secrets"
}

output "infrastructure_secrets" {
  value       = {
    for key, secret in google_secret_manager_secret.infrastructure_secrets :
    key => secret.id
  }
  description = "The IDs of infrastructure secrets"
}

output "gcp_secrets" {
  value       = {
    for key, secret in google_secret_manager_secret.gcp_secrets :
    key => secret.id
  }
  description = "The IDs of GCP configuration secrets"
}
