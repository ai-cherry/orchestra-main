# Redis Module for AI Orchestra
# Provides a Redis instance for task queues and distributed coordination

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for the Redis instance"
  type        = string
  default     = "us-west4"
}

variable "redis_name" {
  description = "Name for the Redis instance"
  type        = string
  default     = "orchestra-redis"
}

variable "redis_tier" {
  description = "The service tier of the instance"
  type        = string
  default     = "BASIC"
}

variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

variable "redis_version" {
  description = "The version of Redis software"
  type        = string
  default     = "REDIS_6_X"
}

variable "network" {
  description = "The VPC network to use"
  type        = string
  default     = "default"
}

variable "authorized_network" {
  description = "The full name of the Google Compute Engine network to which the instance is connected"
  type        = string
  default     = null
}

variable "connect_mode" {
  description = "The connection mode of the Redis instance"
  type        = string
  default     = "DIRECT_PEERING"
}

variable "redis_configs" {
  description = "Redis configuration parameters"
  type        = map(string)
  default     = {
    "maxmemory-policy" = "allkeys-lru"
  }
}

variable "labels" {
  description = "Resource labels"
  type        = map(string)
  default     = {
    "environment" = "production"
    "application" = "ai-orchestra"
  }
}

resource "google_redis_instance" "redis" {
  name           = var.redis_name
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region
  project        = var.project_id
  
  redis_version  = var.redis_version
  
  authorized_network = var.authorized_network
  connect_mode       = var.connect_mode
  
  redis_configs = var.redis_configs
  
  labels = var.labels
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SATURDAY"
      start_time {
        hours = 2
        minutes = 0
      }
    }
  }
  
  lifecycle {
    prevent_destroy = false
  }
}

output "redis_host" {
  value = google_redis_instance.redis.host
  description = "The IP address of the Redis instance"
}

output "redis_port" {
  value = google_redis_instance.redis.port
  description = "The port of the Redis instance"
}

output "redis_id" {
  value = google_redis_instance.redis.id
  description = "The ID of the Redis instance"
}

output "redis_name" {
  value = google_redis_instance.redis.name
  description = "The name of the Redis instance"
}