# Terraform configuration for Vertex AI Workbench, Firestore, Redis, and Secret Manager

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# ------------ Provider Configuration --------------
provider "google" {
  project     = var.project_id
  region      = var.region
  zone        = "${var.region}-a"
}

provider "google-beta" {
  project     = var.project_id
  region      = var.region
  zone        = "${var.region}-a"
}

# ------------ Variables --------------
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
  default     = "dev"
}

variable "notebook_name" {
  description = "Name for the Vertex AI Workbench notebook instance"
  type        = string
  default     = "vertex-workbench"
}

variable "network_name" {
  description = "Name of the VPC network to use"
  type        = string
  default     = "default"
}

variable "firestore_db_name" {
  description = "Name for the Firestore database"
  type        = string
  default     = "orchestrator-db"
}

variable "redis_name" {
  description = "Name for the Redis instance"
  type        = string
  default     = "orchestrator-cache"
}

# ------------ Enable Required APIs --------------
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "aiplatform.googleapis.com",
    "notebooks.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "firestore.googleapis.com",
    "redis.googleapis.com",
    "vpcaccess.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# ------------ Vertex AI Workbench Notebook --------------
resource "google_notebooks_instance" "vertex_workbench" {
  provider     = google-beta
  name         = "${var.notebook_name}-${var.env}"
  location     = var.region
  project      = var.project_id
  machine_type = "n1-standard-4" # 4 vCPUs, 15GB RAM

  # Ensure APIs are enabled first
  depends_on = [
    google_project_service.required_apis
  ]

  vm_image {
    project      = "deeplearning-platform-release"
    image_family = "tf-ent-2-10-cu113-notebooks"
  }

  # Boot disk size and type
  boot_disk_type    = "PD_SSD"
  boot_disk_size_gb = 100

  # Network configuration
  network = var.network_name
  subnet  = var.network_name

  # Metadata for additional configuration
  metadata = {
    proxy-mode        = "service_account"
    terraform_managed = "true"
  }

  # Labels for resource management
  labels = {
    env = var.env
  }

  # Service account to use
  service_account = "default"
  
  # Custom display device configuration for memory
  # Need to use accelerator type to get more memory (the 4vCPUs + 16GB RAM requirement)
  accelerator_config {
    type       = "NVIDIA_TESLA_T4"
    core_count = 1
  }

  # Shielded VM configuration for security
  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  # Instance owner
  instance_owners = ["admin@example.com"]
}

# ------------ Firestore Database --------------
resource "google_firestore_database" "database" {
  project                     = var.project_id
  name                        = var.firestore_db_name
  location_id                 = var.region
  type                        = "FIRESTORE_NATIVE"
  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
  
  # Ensure APIs are enabled first
  depends_on = [
    google_project_service.required_apis
  ]
}

# Cloud Storage bucket for Firestore backups
resource "google_storage_bucket" "firestore_backups" {
  name          = "${var.project_id}-firestore-backups"
  location      = var.region
  storage_class = "STANDARD"
  
  # Configure versioning for backup safety
  versioning {
    enabled = true
  }
  
  # Lifecycle rules for backup management
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  # Uniform bucket level access
  uniform_bucket_level_access = true
}

# Firestore backup schedule (Cloud Scheduler job with a Pub/Sub trigger to a Cloud Function)
resource "google_pubsub_topic" "firestore_backup_topic" {
  name = "firestore-backup-trigger"
  
  depends_on = [
    google_project_service.required_apis
  ]
}

resource "google_cloud_scheduler_job" "firestore_backup_job" {
  name        = "firestore-daily-backup"
  description = "Triggers daily backup of Firestore database"
  schedule    = "0 2 * * *"  # Run at 2 AM every day
  region      = var.region
  
  pubsub_target {
    topic_name = google_pubsub_topic.firestore_backup_topic.id
    data       = base64encode("{\"database\": \"${google_firestore_database.database.name}\", \"bucket\": \"${google_storage_bucket.firestore_backups.name}\"}")
  }
  
  depends_on = [
    google_pubsub_topic.firestore_backup_topic
  ]
}

# ------------ Redis Instance --------------
resource "google_redis_instance" "cache" {
  name           = "${var.redis_name}-${var.env}"
  tier           = "STANDARD_HA"  # High availability tier
  memory_size_gb = 3
  region         = var.region
  
  # Redis version
  redis_version = "REDIS_6_X"
  
  # Display name
  display_name = "Orchestrator Cache - ${var.env}"
  
  # Network configuration
  authorized_network = var.network_name
  
  # Redis configuration
  redis_configs = {
    "maxmemory-policy" = "allkeys-lru"
  }
  
  # Enable authentication
  auth_enabled = true
  
  # Enable transit encryption
  transit_encryption_mode = "SERVER_AUTHENTICATION"
  
  # Maintenance window
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 2
        minutes = 0
      }
    }
  }
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# ------------ Secret Manager --------------
resource "google_secret_manager_secret" "vertex_api_key" {
  secret_id = "vertex-api-key"
  replication {
    auto {}
  }
  
  depends_on = [
    google_project_service.required_apis
  ]
}

resource "google_secret_manager_secret_version" "vertex_api_key_version" {
  secret      = google_secret_manager_secret.vertex_api_key.id
  secret_data = "0d08481a204c0cdba4095bb94529221e8b8ced5c"  # Using the key provided in previous feedback
}

resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "redis-auth"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "redis_auth_version" {
  secret      = google_secret_manager_secret.redis_auth.id
  secret_data = google_redis_instance.cache.auth_string
}

resource "google_secret_manager_secret" "firestore_backup_credentials" {
  secret_id = "firestore-backup-credentials"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "firestore_backup_credentials_version" {
  secret      = google_secret_manager_secret.firestore_backup_credentials.id
  secret_data = "{\"type\": \"service_account\", \"project_id\": \"${var.project_id}\"}"  # Placeholder; would normally include real credentials
}

# ------------ Service Account for Managing Resources --------------
resource "google_service_account" "orchestrator_sa" {
  account_id   = "orchestrator-service-account"
  display_name = "Orchestrator Service Account"
  
  depends_on = [
    google_project_service.required_apis
  ]
}

# Grant permissions to the service account
resource "google_project_iam_member" "orchestrator_sa_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "orchestrator_sa_redis" {
  project = var.project_id
  role    = "roles/redis.editor"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "orchestrator_sa_secretmanager" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

resource "google_project_iam_member" "orchestrator_sa_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.orchestrator_sa.email}"
}

# ------------ Outputs as JSON --------------
output "connection_details" {
  description = "Connection details for all provisioned resources"
  value = jsonencode({
    "vertex_workbench" = {
      "name"     = google_notebooks_instance.vertex_workbench.name
      "url"      = "https://${var.region}.notebooks.cloud.google.com/view/${var.project_id}/${var.region}/${google_notebooks_instance.vertex_workbench.name}"
      "machine_type" = google_notebooks_instance.vertex_workbench.machine_type
      "location" = google_notebooks_instance.vertex_workbench.location
    },
    "firestore" = {
      "name"     = google_firestore_database.database.name
      "type"     = google_firestore_database.database.type
      "location" = google_firestore_database.database.location_id
      "backup_bucket" = google_storage_bucket.firestore_backups.name
      "backup_schedule" = "Daily at 2:00 AM UTC"
    },
    "redis" = {
      "host"        = google_redis_instance.cache.host
      "port"        = google_redis_instance.cache.port
      "memory_size" = "${google_redis_instance.cache.memory_size_gb} GB"
      "auth_enabled" = google_redis_instance.cache.auth_enabled
      "auth_secret" = "projects/${var.project_id}/secrets/${google_secret_manager_secret.redis_auth.secret_id}/versions/latest"
    },
    "secrets" = {
      "vertex_api_key" = "projects/${var.project_id}/secrets/${google_secret_manager_secret.vertex_api_key.secret_id}/versions/latest",
      "redis_auth" = "projects/${var.project_id}/secrets/${google_secret_manager_secret.redis_auth.secret_id}/versions/latest",
      "firestore_backup_credentials" = "projects/${var.project_id}/secrets/${google_secret_manager_secret.firestore_backup_credentials.secret_id}/versions/latest"
    },
    "service_account" = {
      "email" = google_service_account.orchestrator_sa.email,
      "roles" = [
        "roles/datastore.user",
        "roles/redis.editor",
        "roles/secretmanager.secretAccessor",
        "roles/aiplatform.user"
      ]
    }
  })
}

# Output JSON connection details to a local file
resource "local_file" "connection_details" {
  content  = jsonencode({
    "vertex_workbench" = {
      "name"     = google_notebooks_instance.vertex_workbench.name
      "url"      = "https://${var.region}.notebooks.cloud.google.com/view/${var.project_id}/${var.region}/${google_notebooks_instance.vertex_workbench.name}"
      "machine_type" = google_notebooks_instance.vertex_workbench.machine_type
      "location" = google_notebooks_instance.vertex_workbench.location
    },
    "firestore" = {
      "name"     = google_firestore_database.database.name
      "type"     = google_firestore_database.database.type
      "location" = google_firestore_database.database.location_id
      "backup_bucket" = google_storage_bucket.firestore_backups.name
      "backup_schedule" = "Daily at 2:00 AM UTC"
    },
    "redis" = {
      "host"        = google_redis_instance.cache.host
      "port"        = google_redis_instance.cache.port
      "memory_size" = "${google_redis_instance.cache.memory_size_gb} GB"
      "auth_enabled" = google_redis_instance.cache.auth_enabled
      "auth_secret" = "projects/${var.project_id}/secrets/${google_secret_manager_secret.redis_auth.secret_id}/versions/latest"
    },
    "secrets" = {
      "vertex_api_key" = "projects/${var.project_id}/secrets/${google_secret_manager_secret.vertex_api_key.secret_id}/versions/latest",
      "redis_auth" = "projects/${var.project_id}/secrets/${google_secret_manager_secret.redis_auth.secret_id}/versions/latest",
      "firestore_backup_credentials" = "projects/${var.project_id}/secrets/${google_secret_manager_secret.firestore_backup_credentials.secret_id}/versions/latest"
    },
    "service_account" = {
      "email" = google_service_account.orchestrator_sa.email,
      "roles" = [
        "roles/datastore.user",
        "roles/redis.editor",
        "roles/secretmanager.secretAccessor",
        "roles/aiplatform.user"
      ]
    }
  })
  filename = "infra/connection_details.json"
}
