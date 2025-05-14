# Performance-optimized Cloud Workstation configuration for AI Orchestra
# This configuration prioritizes high-performance development with GPU acceleration

# Variable declarations
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "GCP Region for workstation cluster"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone for workstation resources"
  type        = string
  default     = "us-central1-a"
}

locals {
  # Performance-optimized workstation settings
  machine_type      = "n2d-standard-32"    # 32 vCPUs, 128GB memory
  boot_disk_size_gb = 200                  # 200GB boot disk
  gpu_type          = "nvidia-tesla-t4"    # T4 GPU for AI workloads
  gpu_count         = 2                    # 2 GPUs for parallel operations
  
  # Network settings
  network    = "default"
  subnetwork = "default"
  
  # Common labels
  common_labels = {
    app         = "ai-orchestra"
    environment = "development"
    managed-by  = "terraform"
  }
}

# VPC for Cloud Workstations
resource "google_compute_network" "workstation_network" {
  name                    = "ai-orchestra-workstation-network"
  project                 = var.project_id
  auto_create_subnetworks = false
}

# Subnet for Cloud Workstations
resource "google_compute_subnetwork" "workstation_subnet" {
  name          = "ai-orchestra-workstation-subnet"
  project       = var.project_id
  ip_cidr_range = "10.2.0.0/16"
  region        = var.region
  network       = google_compute_network.workstation_network.id
  
  # Enable private Google access for better performance
  private_ip_google_access = true
}

# Cloud Workstation Cluster
resource "google_workstations_workstation_cluster" "cluster" {
  provider               = google-beta
  project                = var.project_id
  workstation_cluster_id = "ai-orchestra-cluster"
  location               = var.region
  network                = google_compute_network.workstation_network.id
  subnetwork             = google_compute_subnetwork.workstation_subnet.id
  
  private_cluster_config {
    enable_private_endpoint = true
  }
  
  labels = local.common_labels
}

# Cloud Workstation Configuration - simplified for compatibility
resource "google_workstations_workstation_config" "optimized_config" {
provider               = google-beta
project                = var.project_id
workstation_config_id  = "ai-orchestra-config"
location               = var.region
workstation_cluster_id = google_workstations_workstation_cluster.cluster.workstation_cluster_id

# Basic configuration that will work with current provider
host {
  # Use GCE instance for workstation with high performance specs
  gce_instance {
    machine_type = local.machine_type
  }
}

# Container for development environment
container {
  image = "gcr.io/${var.project_id}/ai-orchestra-workstation:latest"
  
  # Environment variables
  env = {
    "ENVIRONMENT"             = "development"
    "VECTOR_LISTS"            = "4000"
    "ENABLE_MCP_MEMORY"       = "true"
    "CONTEXT_OPTIMIZATION"    = "maximum"
    "PYTHONUNBUFFERED"        = "1"
    "PYTHONDONTWRITEBYTECODE" = "1"
    "HOME"                    = "/home/user"
  }
    
    # Resource limits
    command = []
    args    = []
  }
  
  # Persistent directory configuration
  persistent_directories {
    mount_path = "/home/user"
    
    gce_pd {
      size_gb       = 100
      fs_type       = "ext4"
      disk_type     = "pd-ssd"
      reclaim_policy = "DELETE"
    }
  }
  
  # Idle timeout settings - slightly longer for AI development
  idle_timeout = "1800s" # 30 minutes
  
  # Running timeout - set to 24 hours for long development sessions
  running_timeout = "86400s" # 24 hours
  
  labels = local.common_labels
}

# Workstation instance
resource "google_workstations_workstation" "developer_workstation" {
  provider               = google-beta
  project                = var.project_id
  workstation_id         = "ai-orchestra-workstation"
  location               = var.region
  workstation_cluster_id = google_workstations_workstation_cluster.cluster.workstation_cluster_id
  workstation_config_id  = google_workstations_workstation_config.optimized_config.workstation_config_id
  
  labels = local.common_labels
}

# IAM binding for workstation access
resource "google_workstations_workstation_iam_binding" "workstation_user" {
  provider = google-beta
  project  = var.project_id
  location = var.region
  workstation_cluster_id = google_workstations_workstation_cluster.cluster.workstation_cluster_id
  workstation_config_id  = google_workstations_workstation_config.optimized_config.workstation_config_id
  workstation_id         = google_workstations_workstation.developer_workstation.workstation_id
  role    = "roles/workstations.user"
  members = [
    "user:YOUR_EMAIL@example.com",
  ]
}

# Allow Vertex AI API access for the workstation
resource "google_project_iam_member" "workstation_vertex_access" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${var.project_id}-compute@developer.gserviceaccount.com"
}

# Firewall rule to allow healthcheck
resource "google_compute_firewall" "allow_health_check" {
  name    = "allow-health-check-workstation"
  network = google_compute_network.workstation_network.id
  project = var.project_id
  
  allow {
    protocol = "tcp"
    ports    = ["22", "3389", "8080"]
  }
  
  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["workstation-vm"]
}

# Outputs
output "workstation_cluster_id" {
  value = google_workstations_workstation_cluster.cluster.workstation_cluster_id
  description = "The workstation cluster ID"
}

output "workstation_config_id" {
  value = google_workstations_workstation_config.optimized_config.workstation_config_id
  description = "The workstation configuration ID"
}

output "workstation_id" {
  value = google_workstations_workstation.developer_workstation.workstation_id
  description = "The workstation ID"
}