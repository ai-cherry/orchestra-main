/**
 * PostgreSQL Cloud SQL Instance with pgvector Support
 *
 * This configuration provisions:
 * - Cloud SQL PostgreSQL database instance suitable for Phidata memory
 * - Enables pgvector extension for vector embeddings storage
 * - Configures simplified backups for development speed
 * - Creates database user with Secret Manager-stored password
 */

# Cloud SQL PostgreSQL Instance with pgvector support
resource "google_sql_database_instance" "phidata_postgres" {
  name             = "phidata-postgres-${var.env}"
  database_version = "POSTGRES_14"
  region           = var.region

  settings {
    tier              = var.env == "prod" ? "db-custom-2-7680" : var.postgres_tier
    availability_type = var.env == "prod" ? "REGIONAL" : var.postgres_availability_type
    
    # Simplified backup configuration for development speed
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "02:00" # 2 AM in UTC
      transaction_log_retention_days = 3
      backup_retention_settings {
        retained_backups = 3
      }
    }
    
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
    
    # PostgreSQL specific database flags optimized for performance
    database_flags {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements,vector"
    }
    
    database_flags {
      name  = "max_connections"
      value = tostring(var.postgres_max_connections)
    }
    
    database_flags {
      name  = "work_mem"
      value = var.postgres_work_mem
    }
    
    database_flags {
      name  = "maintenance_work_mem"
      value = var.postgres_maintenance_mem
    }
    
    database_flags {
      name  = "effective_cache_size"
      value = "1GB"  # Optimized for performance
    }
  }
  
  # Disabled for easier development
  deletion_protection = false
  depends_on          = [google_project_service.required_apis]
  
  lifecycle {
    prevent_destroy = false  # Allow destruction for development
  }
}

# Create phidata_memory database
resource "google_sql_database" "phidata_memory" {
  name     = "phidata_memory"
  instance = google_sql_database_instance.phidata_postgres.name
}

# Generate random password for database user
resource "random_password" "postgres_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Create database user
resource "google_sql_user" "phidata_user" {
  name     = "phidata_user"
  instance = google_sql_database_instance.phidata_postgres.name
  password = random_password.postgres_password.result
}

# Store database password in Secret Manager
resource "google_secret_manager_secret" "postgres_password" {
  secret_id = "postgres-password-${var.env}"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "postgres_password_value" {
  secret      = google_secret_manager_secret.postgres_password.id
  secret_data = random_password.postgres_password.result
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "postgres_secret_access" {
  secret_id = google_secret_manager_secret.postgres_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.orchestra_service_account.email}"
}

# Output PostgreSQL connection details
output "postgresql_connection" {
  value = {
    instance_connection_name = google_sql_database_instance.phidata_postgres.connection_name
    database                 = google_sql_database.phidata_memory.name
    username                 = google_sql_user.phidata_user.name
    password_secret          = google_secret_manager_secret.postgres_password.name
  }
  sensitive = true
}

output "postgres_connection_name" {
  value     = google_sql_database_instance.phidata_postgres.connection_name
  sensitive = false
}

output "postgres_database" {
  value     = google_sql_database.phidata_memory.name
  sensitive = false
}

output "postgres_user" {
  value     = google_sql_user.phidata_user.name
  sensitive = false
}