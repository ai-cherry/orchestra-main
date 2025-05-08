# Performance-optimized database configuration for AI Orchestra

# Redis Cache for Memory System
resource "google_redis_instance" "memory_cache" {
  name           = "memory-cache-${var.env}"
  tier           = "STANDARD_HA"
  memory_size_gb = 8
  region         = var.region
  
  redis_version     = "REDIS_6_X"
  display_name      = "MCP Memory Cache"
  reserved_ip_range = "10.0.0.0/29"
  
  # Redis configuration
  redis_configs = {
    "maxmemory-policy"            = "allkeys-lru"
    "notify-keyspace-events"      = "KEA"
    "timeout"                     = "3600"
    "maxmemory-samples"           = "5"
    "activedefrag"                = "yes"
    "latency-monitor-threshold"   = "25"
    "lazyfree-lazy-eviction"      = "yes"
    "lazyfree-lazy-expire"        = "yes"
    "lazyfree-lazy-server-del"    = "yes"
  }
  
  # Maintenance policy
  maintenance_policy {
    weekly_maintenance_window {
      day = "SATURDAY"
      start_time {
        hours = 2
        minutes = 0
      }
    }
  }
  
  # Labels
  labels = {
    environment = var.env
    managed-by  = "terraform"
    project     = "ai-orchestra"
  }
}

# Firestore Database Configuration
resource "google_firestore_database" "memory_store" {
  name        = "memory-store"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  
  # Optimized for memory operations
  concurrency_mode = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# Firestore Index for Vector Search
resource "google_firestore_index" "memory_vector_index" {
  collection = "memory_entries"
  
  # Note: Vector search might require a different approach
  fields {
    field_path = "embedding"
    order      = "ASCENDING"
  }
  
  fields {
    field_path = "metadata.context_relevance"
    order      = "DESCENDING"
  }
  
  fields {
    field_path = "priority"
    order      = "DESCENDING"
  }
  
  fields {
    field_path = "metadata.last_accessed"
    order      = "DESCENDING"
  }
  
  depends_on = [
    google_firestore_database.memory_store
  ]
}

# AlloyDB Cluster for Cold Storage
resource "google_alloydb_cluster" "memory_cold_storage" {
  cluster_id = "memory-cold-storage-${var.env}"
  location   = var.region
  # Network configuration is handled differently for AlloyDB
  
  
  # Labels
  labels = {
    environment = var.env
    managed-by  = "terraform"
    project     = "ai-orchestra"
  }
  
  initial_user {
    user     = "memory-admin"
    password = "PLACEHOLDER_TO_BE_REPLACED_WITH_SECRET"
  }
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# AlloyDB Instance for Cold Storage
resource "google_alloydb_instance" "memory_cold_storage_primary" {
  cluster       = google_alloydb_cluster.memory_cold_storage.name
  instance_id   = "memory-cold-storage-primary"
  instance_type = "PRIMARY"
  
  machine_config {
    cpu_count = 8
  }
  
  database_flags = {
    "max_connections"                  = "1000"
    "shared_buffers"                   = "8GB"
    "work_mem"                         = "64MB"
    "maintenance_work_mem"             = "512MB"
    "effective_cache_size"             = "24GB"
    "random_page_cost"                 = "1.1"
    "effective_io_concurrency"         = "200"
    "max_worker_processes"             = "8"
    "max_parallel_workers_per_gather"  = "4"
    "max_parallel_workers"             = "8"
    "max_parallel_maintenance_workers" = "4"
    "autovacuum_vacuum_scale_factor"   = "0.05"
    "autovacuum_analyze_scale_factor"  = "0.025"
  }
  
  depends_on = [
    google_alloydb_cluster.memory_cold_storage
  ]
}

# Secret for AlloyDB Password
resource "google_secret_manager_secret" "alloydb_password" {
  secret_id = "alloydb-password-${var.env}"
  
  replication {
    auto {}
  }
  
  labels = {
    environment = var.env
    managed-by  = "terraform"
    project     = "ai-orchestra"
  }
}

# IAM binding for AlloyDB Password
resource "google_secret_manager_secret_iam_binding" "alloydb_password_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.alloydb_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.cloud_run_sa.email}",
  ]
}

# Outputs
output "redis_host" {
  description = "The host of the Redis instance"
  value       = google_redis_instance.memory_cache.host
}

output "redis_port" {
  description = "The port of the Redis instance"
  value       = google_redis_instance.memory_cache.port
}

output "firestore_database_name" {
  description = "The name of the Firestore database"
  value       = google_firestore_database.memory_store.name
}

output "alloydb_connection_name" {
  description = "The connection name of the AlloyDB instance"
  value       = google_alloydb_instance.memory_cold_storage_primary.name
}