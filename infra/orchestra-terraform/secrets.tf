/**
 * Orchestra Secrets Management
 * 
 * This configuration manages API keys and sensitive configuration as Secret Manager resources.
 * It maintains compatibility with environment variables while adding secure secret access.
 */

# LLM API Keys
resource "google_secret_manager_secret" "llm_api_keys" {
  for_each = {
    "anthropic-api-key"        = "Anthropic API key for Claude models"
    "openai-api-key"           = "OpenAI API key for GPT models" 
    "openrouter-api-key"       = "OpenRouter API key for multi-model access"
    "mistral-api-key"          = "Mistral AI API key"
    "together-ai-api-key"      = "Together.ai API key"
    "deepseek-api-key"         = "DeepSeek AI API key"
    "perplexity-api-key"       = "Perplexity AI API key"
    "cohere-api-key"           = "Cohere API key"
    "huggingface-api-token"    = "HuggingFace API token"
    "eleven-labs-api-key"      = "ElevenLabs API key for voice synthesis"
  }
  
  secret_id = "${each.key}-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = {
    category = "llm-api-keys"
    env      = var.env
  }
  
  depends_on = [google_project_service.required_apis]
  
  lifecycle {
    ignore_changes = [
      replication,
      labels
    ]
  }
}

# Data Services & Tools API Keys
resource "google_secret_manager_secret" "tools_api_keys" {
  for_each = {
    "portkey-api-key"            = "Portkey API key for LLM routing"
    "apify-api-token"            = "Apify API token for web scraping"
    "apollo-io-api-key"          = "Apollo.io API key"
    "brave-api-key"              = "Brave Search API key"
    "exa-api-key"                = "Exa API key"
    "eden-ai-api-key"            = "Eden AI API key"
    "langsmith-api-key"          = "LangSmith API key"
    "notion-api-key"             = "Notion API key"
    "phantom-buster-api-key"     = "PhantomBuster API key"
    "pinecone-api-key"           = "Pinecone vector DB API key"
    "sourcegraph-access-token"   = "Sourcegraph access token"
    "tavily-api-key"             = "Tavily API key for search"
    "twingly-api-key"            = "Twingly API key"
    "zenrows-api-key"            = "ZenRows API key for web scraping"
  }
  
  secret_id = "${each.key}-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = {
    category = "tools-api-keys"
    env      = var.env
  }
  
  depends_on = [google_project_service.required_apis]
  
  lifecycle {
    ignore_changes = [
      replication,
      labels
    ]
  }
}

# GCP Configuration Secrets
resource "google_secret_manager_secret" "gcp_secrets" {
  for_each = {
    "gcp-client-secret"       = "GCP OAuth client secret"
    "gcp-service-account-key" = "GCP service account key"
    "vertex-agent-key"        = "Vertex AI agent key"
  }
  
  secret_id = "${each.key}-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = {
    category = "gcp-configuration"
    env      = var.env
  }
  
  depends_on = [google_project_service.required_apis]
  
  lifecycle {
    ignore_changes = [
      replication,
      labels
    ]
  }
}

# Service Account for accessing secrets
resource "google_service_account" "secret_accessor" {
  account_id   = "orchestra-secret-accessor-${var.env}"
  display_name = "Orchestra Secret Accessor"
  description  = "Service account for accessing sensitive configuration in Secret Manager"
  
  lifecycle {
    ignore_changes = [
      display_name,
      description
    ]
  }
}

# Grant secret access to the service account
resource "google_secret_manager_secret_iam_binding" "secret_accessor_binding_llm" {
  for_each  = google_secret_manager_secret.llm_api_keys
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  members   = [
    "serviceAccount:${google_service_account.secret_accessor.email}",
    "serviceAccount:${google_service_account.cloud_run_identity.email}"
  ]
}

resource "google_secret_manager_secret_iam_binding" "secret_accessor_binding_tools" {
  for_each  = google_secret_manager_secret.tools_api_keys
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  members   = [
    "serviceAccount:${google_service_account.secret_accessor.email}",
    "serviceAccount:${google_service_account.cloud_run_identity.email}"
  ]
}

resource "google_secret_manager_secret_iam_binding" "secret_accessor_binding_gcp" {
  for_each  = google_secret_manager_secret.gcp_secrets
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  members   = [
    "serviceAccount:${google_service_account.secret_accessor.email}",
    "serviceAccount:${google_service_account.cloud_run_identity.email}"
  ]
}

# Output secret details
output "managed_secrets" {
  description = "Information about managed secrets in Secret Manager"
  value = {
    llm_api_keys = {
      for key, secret in google_secret_manager_secret.llm_api_keys : 
      key => "${secret.name}/versions/latest"
    }
    tools_api_keys = {
      for key, secret in google_secret_manager_secret.tools_api_keys : 
      key => "${secret.name}/versions/latest"
    }
    gcp_secrets = { 
      for key, secret in google_secret_manager_secret.gcp_secrets : 
      key => "${secret.name}/versions/latest"
    }
    secret_accessor_service_account = google_service_account.secret_accessor.email
  }
  sensitive = true
}
