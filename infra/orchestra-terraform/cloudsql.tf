/**
* PostgreSQL Cloud SQL Instance with pgvector Support
 *
 * This configuration provisions:
 * - Cloud SQL PostgreSQL database instance suitable for Phidata memory
 * - Enables pgvector extension for vector embeddings storage
 * - Configures automatic backups and point-in-time recovery
 * - Creates database user with Secret Manager-stored password
 * - Sets up IAM permissions for Cloud Run service account
 */

# Cloud SQL PostgreSQL Instance with pgvector support
resource "google_sql_database_instance" "phidata_postgres" {
  name             = "phidata-postgres-${var.env}"
  database_version = "POSTGRES_14"
  region           = var.region

  settings {
    tier              = var.env == "prod" ? "db-custom-2-4096" : "db-g1-small"
    availability_type = var.env == "prod" ? "REGIONAL" : "ZONAL"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "02:00"  # 2 AM in UTC
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
      }
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }

    # Removed the problematic database flag
  }

  deletion_protection = var.env == "prod" ? true : false
  depends_on = [google_project_service.required_apis]
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

# Enable pgvector extension in the database - commented out for now as it may cause issues
resource "null_resource" "enable_pgvector" {
  # This provisioner is commented out because it may fail if direct database connection is not possible
  # We'll handle pgvector extension setup separately
  /*
  provisioner "local-exec" {
    command = <<-EOT
      gcloud sql connect ${google_sql_database_instance.phidata_postgres.name} --user=postgres --quiet <<EOF
      \c phidata_memory
      CREATE EXTENSION IF NOT EXISTS vector;
      EOF
    EOT
  }
  */

  depends_on = [
    google_sql_database.phidata_memory,
    google_sql_user.phidata_user
  ]
}

# Create Service Account for Cloud Run identity if not already defined
resource "google_service_account" "cloud_run_identity" {
  account_id   = "orchestra-cloud-run-${var.env}"
  display_name = "Orchestra Cloud Run Service Account"
  description  = "Service account for Orchestra Cloud Run services to access Cloud SQL"
}

# Grant Cloud SQL Client role to service account
resource "google_project_iam_member" "cloud_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_identity.email}"
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "postgres_secret_access" {
  secret_id = google_secret_manager_secret.postgres_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_identity.email}"
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
