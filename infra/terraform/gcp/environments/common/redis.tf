/**
 * Redis configuration for common environment
 */

# Redis instance for Orchestra caching
resource "google_redis_instance" "orchestra-redis-cache" {
  name           = "orchestra-redis-cache"
  project        = var.project_id
  region         = "us-west4"
  tier           = "BASIC"
  memory_size_gb = 1
  
  # Network configuration
  authorized_network = "default"
  
  # Redis version and other configurations
  redis_version     = "REDIS_6_X"
  display_name      = "Orchestra Redis Cache"
  
  # Standard settings for basic tier
  connect_mode       = "DIRECT_PEERING"
  redis_configs      = {
    "maxmemory-policy" = "allkeys-lru"
  }
  
  # Optional but recommended settings
  labels = {
    environment = "common"
    service     = "orchestra"
  }
}

# Output the Redis connection information for reference
output "redis_host" {
  value       = google_redis_instance.orchestra-redis-cache.host
  description = "The IP address of the Redis instance"
}

output "redis_port" {
  value       = google_redis_instance.orchestra-redis-cache.port
  description = "The port of the Redis instance"
}
