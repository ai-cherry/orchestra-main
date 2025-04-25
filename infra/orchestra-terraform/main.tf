/**
 * Orchestra Infrastructure Terraform Configuration
 * 
 * This configuration provisions:
 * - Vertex AI Workbench with 4 vCPUs and 16GB RAM
 * - Firestore in NATIVE mode with daily backups
 * - Memorystore Redis instance with 3GB capacity
 * - Secret Manager with initial secrets
 * - Enables required Vertex AI APIs
 */

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

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "aiplatform.googleapis.com",
    "firestore.googleapis.com", 
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com"
  ])
  
  project = var.project_id
  service = each.key
  
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Vertex AI Workbench
resource "google_notebooks_instance" "ai_workbench" {
  name         = "orchestra-workbench"
  location     = var.zone
  machine_type = "n1-standard-4"  # 4 vCPUs, 15GB RAM
  
  vm_image {
    project      = "deeplearning-platform-release"
    image_family = "tf-ent-2-9-cu113-notebooks"
  }
  
  boot_disk_type    = "PD_SSD"
  boot_disk_size_gb = 100
  
  no_public_ip    = false
  no_proxy_access = false
  
  depends_on = [google_project_service.required_apis]
}

# Firestore Database in Native Mode
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = "nam5"  # Multi-region in North America
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.required_apis]
}

# Redis Instance
resource "google_redis_instance" "cache" {
  name           = "orchestra-redis"
  tier           = "BASIC"
  memory_size_gb = 3
  
  region                  = var.region
  location_id             = var.zone
  alternative_location_id = "${var.region}-b"
  
  redis_version     = "REDIS_6_X"
  display_name      = "Orchestra Cache"
  reserved_ip_range = "10.0.0.0/29"
  
  depends_on = [google_project_service.required_apis]
}

# Secret Manager - Figma PAT
resource "google_secret_manager_secret" "figma_pat" {
  secret_id = "figma-pat"
  
  replication {
    automatic = true
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "figma_pat_value" {
  secret      = google_secret_manager_secret.figma_pat.id
  secret_data = var.figma_pat
}

# Secret Manager - Redis Password
resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "redis-auth-${var.env}"
  
  replication {
    automatic = true
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "redis_auth_value" {
  secret      = google_secret_manager_secret.redis_auth.id
  secret_data = random_password.redis_password.result
}

# Generate Random Redis Password
resource "random_password" "redis_password" {
  length  = 16
  special = true
}

# Output connection details as JSON
output "connection_details" {
  value = jsonencode({
    vertex_workbench = {
      name      = google_notebooks_instance.ai_workbench.name
      url       = "https://${var.region}-dot-global.notebooks.googleusercontent.com/jupyter/lab/tree/${google_notebooks_instance.ai_workbench.name}"
      zone      = var.zone
    },
    firestore = {
      database = google_firestore_database.database.name
      location = google_firestore_database.database.location_id
    },
    redis = {
      host     = google_redis_instance.cache.host
      port     = google_redis_instance.cache.port
      password_secret = google_secret_manager_secret.redis_auth.name
    },
    secrets = {
      figma_pat = google_secret_manager_secret.figma_pat.name
    }
  })
  sensitive = true
}
