/**
 * Redis configuration for common environment
 */

# Redis instance for Orchestra caching
resource "google_redis_instance" "orchestra-redis-cache" {
  name           = "${local.env_prefix}-redis-cache"
  project        = var.project_id
  region         = var.region
  tier           = "BASIC"
  memory_size_gb = var.redis_memory_size_gb
  
  # Network configuration
  authorized_network = "default"
  
  # Redis version and other configurations
  redis_version     = "REDIS_6_X"
  display_name      = "Orchestra Redis Cache"
  
  # Standard settings for basic tier
  connect_mode       = "DIRECT_PEERING"
  redis_configs      = {
    "maxmemory-policy" = "allkeys-lru"
    "notify-keyspace-events" = "KEA"
    "timeout" = "300"
  }
  
  # Optional but recommended settings
  labels = merge(local.common_labels, {
    service = "redis-cache"
  })
  
  # Maintenance window (recommended for production)
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours = 2    # 2 AM
        minutes = 0
      }
    }
  }
}

# Outputs moved to outputs.tf
