variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

variable "network_id" {
  description = "VPC Network ID"
  type        = string
}

variable "reserved_ip_range" {
  description = "Reserved IP range for Redis instances"
  type        = string
  default     = ""  # Will use the default allocated by GCP if not provided
}

variable "memory_size_gb" {
  description = "Memory size in GB for Redis instance"
  type        = number
  default     = 1  # 1GB default for dev, adjust for prod
}

variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "REDIS_6_X"
}

# Enable Redis API
resource "google_project_service" "redis_api" {
  project = var.project_id
  service = "redis.googleapis.com"
  
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Create Redis instance for caching and session management
resource "google_redis_instance" "cache" {
  name               = "orchestrator-cache-${var.env}"
  tier               = var.env == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb     = var.env == "prod" ? var.memory_size_gb * 2 : var.memory_size_gb
  region             = var.region
  redis_version      = var.redis_version
  display_name       = "Orchestra ${var.env} Cache"
  
  # Set reserved IP range if provided, otherwise let GCP allocate one
  reserved_ip_range  = var.reserved_ip_range != "" ? var.reserved_ip_range : null
  
  # Network configuration - connect to the VPC network
  authorized_network = var.network_id
  
  # Authentication - enable strong authentication
  auth_enabled       = true
  
  # Redis configs
  redis_configs = {
    maxmemory-policy  = "volatile-lru"  # LRU eviction for keys with TTL
    notify-keyspace-events = "Ex"       # Enable keyspace notifications for expiring keys
    maxmemory-clients = "50"            # Limit memory usage per client
  }
  
  # Labels
  labels = {
    environment = var.env
    service     = "orchestrator"
    usage       = "cache"
  }
  
  # Maintenance settings
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 2  # 2 AM
        minutes = 0
      }
    }
  }
  
  # Transit encryption - enabled by default
  
  depends_on = [
    google_project_service.redis_api
  ]
}

# Create a secret in Secret Manager for Redis AUTH password
resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "redis-auth-${var.env}"
  
  replication {
    automatic = true
  }
  
  labels = {
    environment = var.env
    service     = "orchestrator"
  }
}

# Generate a random password for Redis
resource "random_password" "redis_password" {
  length           = 20
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store the Redis password in Secret Manager
resource "google_secret_manager_secret_version" "redis_auth_version" {
  secret      = google_secret_manager_secret.redis_auth.id
  secret_data = random_password.redis_password.result
}

# Output the Redis instance details
output "redis_host" {
  value       = google_redis_instance.cache.host
  description = "The IP address of the Redis instance"
}

output "redis_port" {
  value       = google_redis_instance.cache.port
  description = "The port of the Redis instance"
}

output "redis_auth_secret" {
  value       = google_secret_manager_secret.redis_auth.name
  description = "The name of the Secret Manager secret containing the Redis AUTH password"
}

output "redis_instance_id" {
  value       = google_redis_instance.cache.id
  description = "The ID of the Redis instance"
}

output "redis_instance_name" {
  value       = google_redis_instance.cache.name
  description = "The name of the Redis instance"
}
