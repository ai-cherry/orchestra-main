/**
 * Secret Manager resources for Orchestra project
 */

# OpenAI API Key
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  project   = var.project_id
  
  replication {
    auto {}
  }
  
  labels = local.common_labels
  
  # Add rotation period recommendation
  # Note: topics field is required but we don't need to specify any topics
  rotation {
    next_rotation_time = timeadd(timestamp(), "8760h") # 1 year from now
    rotation_period    = "31536000s" # 1 year in seconds
    topics             = []
  }
}

# Anthropic API Key
resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  project   = var.project_id
  
  replication {
    auto {}
  }
  
  labels = local.common_labels
  
  # Add rotation period recommendation
  rotation {
    next_rotation_time = timeadd(timestamp(), "8760h") # 1 year from now
    rotation_period    = "31536000s" # 1 year in seconds
  }
}

# Redis Auth String
resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "redis-auth"
  project   = var.project_id
  
  replication {
    auto {}
  }
  
  labels = local.common_labels
  
  # Add rotation period recommendation
  rotation {
    next_rotation_time = timeadd(timestamp(), "8760h") # 1 year from now
    rotation_period    = "31536000s" # 1 year in seconds
  }
}

# Vertex AI API Key
resource "google_secret_manager_secret" "vertex_api_key" {
  secret_id = "vertex-api-key"
  project   = var.project_id
  
  replication {
    auto {}
  }
  
  labels = local.common_labels
  
  # Add rotation period recommendation
  rotation {
    next_rotation_time = timeadd(timestamp(), "8760h") # 1 year from now
    rotation_period    = "31536000s" # 1 year in seconds
    topics             = []
  }
}

# Function to create environment-specific secrets
locals {
  environments = ["dev", "prod"]
  secret_types = {
    "openai-api-key"    = "OpenAI API Key",
    "anthropic-api-key" = "Anthropic API Key",
    "redis-auth"        = "Redis Authentication",
    "vertex-api-key"    = "Vertex AI API Key"
  }
}

# Create environment-specific secrets dynamically
resource "google_secret_manager_secret" "env_secrets" {
  for_each = {
    for pair in setproduct(local.environments, keys(local.secret_types)) :
    "${pair[1]}-${pair[0]}" => {
      env         = pair[0]
      secret_type = pair[1]
      description = local.secret_types[pair[1]]
    }
  }
  
  secret_id = each.key
  project   = var.project_id
  
  replication {
    auto {}
  }
  
  labels = merge(local.common_labels, {
    environment = each.value.env
  })
  
  # Add rotation period recommendation
  rotation {
    next_rotation_time = timeadd(timestamp(), "8760h") # 1 year from now
    rotation_period    = "31536000s" # 1 year in seconds
    topics             = []
  }
}

# Create IAM bindings for the secrets
resource "google_secret_manager_secret_iam_binding" "secret_accessor" {
  for_each  = toset([
    google_secret_manager_secret.openai_api_key.id,
    google_secret_manager_secret.anthropic_api_key.id,
    google_secret_manager_secret.redis_auth.id,
    google_secret_manager_secret.vertex_api_key.id
  ])
  
  secret_id = each.key
  role      = "roles/secretmanager.secretAccessor"
  members   = [
    "serviceAccount:${google_service_account.orchestra_runner_sa.email}"
  ]
}

# Output secret references moved to outputs.tf
