/**
 * Secret Manager resources for Orchestra project
 */

# OpenAI API Key
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "common"
    managed-by  = "terraform"
  }
}

# Anthropic API Key
resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "common"
    managed-by  = "terraform"
  }
}

# Redis Auth String
resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "redis-auth"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "common"
    managed-by  = "terraform"
  }
}

# Environment-specific versions of secrets
# Dev environment
resource "google_secret_manager_secret" "openai_api_key_dev" {
  secret_id = "openai-api-key-dev"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "dev"
    managed-by  = "terraform"
  }
}

resource "google_secret_manager_secret" "anthropic_api_key_dev" {
  secret_id = "anthropic-api-key-dev"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "dev"
    managed-by  = "terraform"
  }
}

resource "google_secret_manager_secret" "redis_auth_dev" {
  secret_id = "redis-auth-dev"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "dev"
    managed-by  = "terraform"
  }
}

# Prod environment
resource "google_secret_manager_secret" "openai_api_key_prod" {
  secret_id = "openai-api-key-prod"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "prod"
    managed-by  = "terraform"
  }
}

resource "google_secret_manager_secret" "anthropic_api_key_prod" {
  secret_id = "anthropic-api-key-prod"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "prod"
    managed-by  = "terraform"
  }
}

resource "google_secret_manager_secret" "redis_auth_prod" {
  secret_id = "redis-auth-prod"
  project   = var.project_id
  
  replication {
    auto {
      customer_managed {
        kms_key_name = null
      }
    }
  }
  
  labels = {
    environment = "prod"
    managed-by  = "terraform"
  }
}

# Output secret references
output "openai_secret_id" {
  value       = google_secret_manager_secret.openai_api_key.id
  description = "ID of the OpenAI API key secret"
}

output "anthropic_secret_id" {
  value       = google_secret_manager_secret.anthropic_api_key.id
  description = "ID of the Anthropic API key secret"
}

output "redis_auth_secret_id" {
  value       = google_secret_manager_secret.redis_auth.id
  description = "ID of the Redis authentication string secret"
}
