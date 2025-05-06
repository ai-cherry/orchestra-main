# Redis configuration for development environment

module "redis" {
  source = "../../modules/redis"
  
  project_id         = var.project_id
  region             = var.region
  redis_name         = "orchestra-redis-dev"
  redis_tier         = "BASIC"
  redis_memory_size_gb = 1
  
  # Use default network for simplicity in dev
  network            = "default"
  
  redis_configs = {
    "maxmemory-policy" = "allkeys-lru"
    "notify-keyspace-events" = "Ex"  # Enable keyspace notifications for expiring keys
  }
  
  labels = {
    "environment" = "development"
    "application" = "ai-orchestra"
    "managed-by"  = "terraform"
  }
}

# Add Redis host and port to Secret Manager
resource "google_secret_manager_secret" "redis_config" {
  secret_id = "redis-config-dev"
  project   = var.project_id
  
  replication {
    automatic = true
  }
  
  labels = {
    "environment" = "development"
    "application" = "ai-orchestra"
  }
}

resource "google_secret_manager_secret_version" "redis_config_version" {
  secret      = google_secret_manager_secret.redis_config.id
  
  secret_data = jsonencode({
    "REDIS_HOST" = module.redis.redis_host,
    "REDIS_PORT" = module.redis.redis_port
  })
}

# Grant access to the Cloud Run service account
resource "google_secret_manager_secret_iam_member" "redis_config_access" {
  secret_id = google_secret_manager_secret.redis_config.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

# Output Redis connection information
output "redis_host" {
  value     = module.redis.redis_host
  sensitive = false
}

output "redis_port" {
  value     = module.redis.redis_port
  sensitive = false
}