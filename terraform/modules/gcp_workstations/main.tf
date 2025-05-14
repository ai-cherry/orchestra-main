# GCP Workstations module for AI Orchestra
# This module creates the necessary infrastructure for GCP Cloud Workstations

# Enable required services first
resource "google_project_service" "required_services" {
  provider = google-beta
  project  = var.project_id
  for_each = toset([
    "workstations.googleapis.com",
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com"
  ])
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Create a service account for the workstation
resource "google_service_account" "workstation_service_account" {
  provider     = google-beta
  account_id   = "orchestra-workstation-${var.environment}"
  display_name = "Orchestra Workstation Service Account"
  project      = var.project_id
  
  depends_on = [
    google_project_service.required_services
  ]
}

# Grant necessary roles to the service account
resource "google_project_iam_member" "workstation_editor_role" {
  provider = google-beta
  project  = var.project_id
  role     = "roles/editor"
  member   = "serviceAccount:${google_service_account.workstation_service_account.email}"
}

resource "google_project_iam_member" "workstation_artifact_reader" {
  provider = google-beta
  project  = var.project_id
  role     = "roles/artifactregistry.reader"
  member   = "serviceAccount:${google_service_account.workstation_service_account.email}"
}

resource "google_project_iam_member" "workstation_aiplatform_user" {
  provider = google-beta
  project  = var.project_id
  role     = "roles/aiplatform.user"
  member   = "serviceAccount:${google_service_account.workstation_service_account.email}"
}

resource "google_project_iam_member" "workstation_secretmanager_accessor" {
  provider = google-beta
  project  = var.project_id
  role     = "roles/secretmanager.secretAccessor"
  member   = "serviceAccount:${google_service_account.workstation_service_account.email}"
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "container_registry" {
  provider      = google-beta
  location      = var.location
  repository_id = "orchestra-container-registry"
  description   = "Docker repository for Orchestra Workstation container images"
  format        = "DOCKER"
  project       = var.project_id

  depends_on = [
    google_project_service.required_services
  ]
}

# Workstation cluster
resource "google_workstations_workstation_cluster" "orchestra_cluster" {
  provider               = google-beta
  name                   = "orchestra-cluster-${var.environment}"
  location               = var.location
  workstation_cluster_id = "orchestra-cluster-${var.environment}"
  project                = var.project_id
  
  network = var.network
  subnetwork = var.subnetwork
  
  private_cluster_config {
    enable_private_endpoint = false
  }

  depends_on = [
    google_project_service.required_services
  ]
}

# Workstation configuration
resource "google_workstations_workstation_config" "orchestra_config" {
  provider = google-beta
  
  name                  = "orchestra-config-${var.environment}"
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  workstation_config_id = "orchestra-config-${var.environment}"
  location              = var.location
  project               = var.project_id

  host {
    gce_instance {
      machine_type = var.machine_type

      shielded_instance_config {
        enable_secure_boot = true
      }

      service_account = google_service_account.workstation_service_account.email
      
      tags = ["workstations"]
    }
  }

  persistent_directories {
    mount_path = "/home/user/.cache"
    gce_pd {
      size_gb        = var.cache_disk_size_gb
      disk_type      = "pd-standard"
      reclaim_policy = "DELETE"
    }
  }

  persistent_directories {
    mount_path = "/home/user/orchestra"
    gce_pd {
      size_gb        = var.data_disk_size_gb
      disk_type      = "pd-ssd"
      reclaim_policy = "DELETE"
    }
  }

  container {
    image = "us-docker.pkg.dev/${var.project_id}/orchestra-container-registry/orchestra-workstation:${var.workstation_image_version}"
    env = {
      "PROJECT_ID" = var.project_id
      "REGION"     = var.location
      "ENV"        = var.environment
    }
    working_dir = "/home/user/orchestra"
    command     = ["/bin/bash", "-c", "/opt/orchestra/startup.sh"]
  }

  idle_timeout = var.idle_timeout
  running_timeout = var.running_timeout

  depends_on = [
    google_workstations_workstation_cluster.orchestra_cluster,
    google_service_account.workstation_service_account,
    google_artifact_registry_repository.container_registry
  ]
}

# Create a workstation instance
resource "google_workstations_workstation" "default_workstation" {
  provider               = google-beta
  name                   = "default-workstation-${var.environment}"
  location               = var.location
  workstation_id         = "default-workstation-${var.environment}"
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  workstation_config_id  = google_workstations_workstation_config.orchestra_config.workstation_config_id
  project                = var.project_id

  depends_on = [
    google_workstations_workstation_config.orchestra_config
  ]
}

# IAM binding to allow users to access workstations
resource "google_workstations_workstation_iam_binding" "workstation_user" {
  provider = google-beta
  project  = var.project_id
  location = var.location
  
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  workstation_config_id  = google_workstations_workstation_config.orchestra_config.workstation_config_id
  workstation_id         = google_workstations_workstation.default_workstation.workstation_id
  
  role = "roles/workstations.user"
  members = var.workstation_users
  
  depends_on = [
    google_workstations_workstation.default_workstation
  ]
}

# Firewall rule to allow HTTP traffic from the workstation cluster
resource "google_compute_firewall" "workstation_http_egress" {
  name    = "allow-workstation-http-egress-${var.environment}"
  network = var.network
  project = var.project_id

  direction = "EGRESS"
  
  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8080", "3000"]
  }

  target_tags = ["workstations"]
  
  depends_on = [
    google_project_service.required_services
  ]
}

# Create a Cloud Storage bucket for workstation data persistence
resource "google_storage_bucket" "workstation_data" {
  name     = "${var.project_id}-orchestra-workstation-data-${var.environment}"
  location = var.location
  project  = var.project_id
  
  force_destroy = false
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
  
  uniform_bucket_level_access = true
}

# IAM binding to allow workstation service account to access the bucket
resource "google_storage_bucket_iam_binding" "workstation_storage_admin" {
  bucket = google_storage_bucket.workstation_data.name
  role   = "roles/storage.admin"
  
  members = [
    "serviceAccount:${google_service_account.workstation_service_account.email}"
  ]
}