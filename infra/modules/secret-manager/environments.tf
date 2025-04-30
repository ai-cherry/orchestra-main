# Environment-specific Secret Manager configuration

# Common secrets for all environments - these will be created with environment-specific suffixes
locals {
  common_secrets = {
    "llm_api_keys" = {
      "openai-api-key"        = "OpenAI API key for GPT models"
      "anthropic-api-key"     = "Anthropic API key for Claude models"
      "openrouter-api-key"    = "OpenRouter API key for multi-model access"
      "mistral-api-key"       = "Mistral AI API key"
      "google-api-key"        = "Google API key for Gemini models"
    }
    "tool_api_keys" = {
      "portkey-api-key"      = "Portkey API key for LLM routing"
      "tavily-api-key"       = "Tavily API key for search"
      "brave-api-key"        = "Brave Search API key"
    }
    "infrastructure" = {
      "redis-auth"           = "Redis authentication credentials"
      "db-credentials"       = "Database credentials"
    }
  }

  # Development-only secrets
  dev_only_secrets = {
    "gcp_secrets" = {
      "service-account-keys" = "Service account keys (dev only)"
    }
    "testing" = {
      "test-data-key"        = "Test data encryption key (dev only)"
      "mock-service-key"     = "Mock service authentication (dev only)"
    }
  }

  # Production-only secrets
  prod_only_secrets = {
    "security" = {
      "oauth-client-secret"     = "OAuth 2.0 client secret for production auth"
      "certificate-key"         = "SSL certificate private key"
    }
    "monitoring" = {
      "alert-webhook-key"       = "Alert notification webhook authentication"
      "monitoring-service-key"  = "Monitoring service authentication"
    }
  }

  # Select environment-specific secrets based on current environment
  env_specific_secrets = var.env == "prod" ? local.prod_only_secrets : local.dev_only_secrets
  
  # Combine common secrets with environment-specific ones - but don't include the other environment's secrets
  all_secrets = merge(local.common_secrets, local.env_specific_secrets)
}

# Service accounts that need access to secrets in each environment
locals {
  # Development environment service accounts
  dev_service_accounts = {
    "orchestra-dev-sa@${var.project_id}.iam.gserviceaccount.com" = [
      "redis-auth-dev",
      "db-credentials-dev",
      "openai-api-key-dev", 
      "anthropic-api-key-dev"
    ]
    "orchestrator-test-sa@${var.project_id}.iam.gserviceaccount.com" = [
      "test-data-key-dev",
      "mock-service-key-dev"
    ]
  }
  
  # Production environment service accounts
  prod_service_accounts = {
    "orchestra-prod-sa@${var.project_id}.iam.gserviceaccount.com" = [
      "redis-auth-prod",
      "db-credentials-prod",
      "openai-api-key-prod", 
      "anthropic-api-key-prod",
      "oauth-client-secret-prod"
    ]
    "orchestrator-monitoring-sa@${var.project_id}.iam.gserviceaccount.com" = [
      "alert-webhook-key-prod",
      "monitoring-service-key-prod"
    ]
  }
  
  # Select the appropriate service accounts based on environment
  service_accounts = var.env == "prod" ? local.prod_service_accounts : local.dev_service_accounts
}

# Create secrets for the current environment from the combined configuration
resource "google_secret_manager_secret" "environment_secrets" {
  for_each = {
    for secret_name, description in flatten([
      for category, secrets in local.all_secrets : [
        for name, desc in secrets : {
          name = name
          desc = desc
          category = category
        }
      ]
    ]) : secret_name => {
      description = description.desc
      category = description.category
    }
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
    purpose     = replace(each.value.category, "_", "-")
    category    = replace(each.value.category, "_", "-")
  }
  
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

# Add IAM bindings for environment-specific service accounts
resource "google_secret_manager_secret_iam_member" "environment_secret_access" {
  for_each = {
    for pair in flatten([
      for sa_email, secret_list in local.service_accounts : [
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

# Output the list of all secrets created for the current environment for validation
output "created_secrets" {
  description = "List of all secrets created for the current environment"
  value = [for secret in google_secret_manager_secret.environment_secrets : secret.secret_id]
}