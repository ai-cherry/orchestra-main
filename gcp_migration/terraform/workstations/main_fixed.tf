# Fixed Terraform configuration for GCP Cloud Workstations
# Resolves structure and attribute issues

variable "project_id" {
  description = "The GCP project ID to deploy resources"
  type        = string
}

variable "location" {
  description = "The GCP region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "network_name" {
  description = "The name of the VPC network to create"
  type        = string
  default     = "workstation-network"
}

variable "subnet_name" {
  description = "The name of the subnet to create"
  type        = string
  default     = "workstation-subnet"
}

variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.2.0.0/16" 
}

variable "workstation_cluster_id" {
  description = "ID for the workstation cluster"
  type        = string
  default     = "orchestra-dev-cluster"
}

variable "standard_config_id" {
  description = "ID for the standard workstation configuration"
  type        = string
  default     = "orchestra-standard-config"
}

variable "ml_config_id" {
  description = "ID for the ML workstation configuration"
  type        = string
  default     = "orchestra-ml-config"
}

variable "persistent_disk_size_gb" {
  description = "Size of the persistent disk in GB"
  type        = number
  default     = 200
}

variable "boot_disk_size_gb" {
  description = "Size of the boot disk in GB"
  type        = number
  default     = 100
}

variable "enable_private_endpoint" {
  description = "Whether to enable private endpoint for the cluster"
  type        = bool
  default     = false
}

variable "disable_public_ip" {
  description = "Whether to disable public IP for the workstation"
  type        = bool
  default     = false
}

variable "standard_machine_type" {
  description = "Machine type for standard workstation"
  type        = string
  default     = "e2-standard-8"
}

variable "ml_machine_type" {
  description = "Machine type for ML workstation"
  type        = string
  default     = "n1-standard-16"
}

variable "enable_gpu" {
  description = "Whether to enable GPU for ML workstation"
  type        = bool
  default     = true
}

variable "gpu_type" {
  description = "Type of GPU to attach to ML workstation"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "gpu_count" {
  description = "Number of GPUs to attach to ML workstation"
  type        = number
  default     = 1
}

# Network resources
resource "google_compute_network" "workstation_network" {
  name                    = var.network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "workstation_subnet" {
  name          = var.subnet_name
  ip_cidr_range = var.subnet_cidr
  network       = google_compute_network.workstation_network.id
  region        = var.location
  
  # Enable Google private access
  private_ip_google_access = true
}

# Add Cloud NAT for outbound connectivity
resource "google_compute_router" "router" {
  name    = "workstation-router"
  network = google_compute_network.workstation_network.id
  region  = var.location
}

resource "google_compute_router_nat" "nat" {
  name                               = "workstation-nat"
  router                             = google_compute_router.router.name
  region                             = var.location
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# Service account for workstations
resource "google_service_account" "workstation_sa" {
  account_id   = "orchestra-workstation-sa"
  display_name = "Orchestra Workstation Service Account"
}

# Grant necessary permissions
resource "google_project_iam_member" "workstation_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.workstation_sa.email}"
}

resource "google_project_iam_member" "workstation_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.workstation_sa.email}"
}

resource "google_project_iam_member" "secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.workstation_sa.email}"
}

# Workstation cluster
resource "google_workstations_workstation_cluster" "orchestra_cluster" {
  workstation_cluster_id = var.workstation_cluster_id
  location               = var.location  # Added required location attribute
  network                = google_compute_network.workstation_network.id
  subnetwork             = google_compute_subnetwork.workstation_subnet.id
  
  private_cluster_config {
    enable_private_endpoint = var.enable_private_endpoint
  }
}

# Standard workstation configuration
resource "google_workstations_workstation_config" "standard_config" {
  workstation_config_id  = var.standard_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  location               = var.location  # Added required location attribute
  
  persistent_directories {
    mount_path = "/home/user/persistent"
    gce_pd {
      size_gb        = var.persistent_disk_size_gb
      reclaim_policy = "DELETE"
    }
  }

  container {
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest"
    
    # Environment variables for AI tools
    env {
      name  = "GEMINI_API_KEY"
      value = "sm://projects/${var.project_id}/secrets/GEMINI_API_KEY/versions/latest"
    }
    env {
      name  = "ENABLE_MCP_MEMORY"
      value = "true"
    }
    
    # Command to run
    command = "code --user-data-dir=/home/user/persistent/.vscode-server"
  }

  host {
    gce_instance {
      machine_type      = var.standard_machine_type
      service_account   = google_service_account.workstation_sa.email
      boot_disk_size_gb = var.boot_disk_size_gb
      disable_public_ip = var.disable_public_ip
    }
  }
}

# ML-optimized workstation configuration
resource "google_workstations_workstation_config" "ml_config" {
  workstation_config_id  = var.ml_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  location               = var.location  # Added required location attribute
  
  persistent_directories {
    mount_path = "/home/user/persistent"
    gce_pd {
      size_gb        = var.persistent_disk_size_gb
      reclaim_policy = "DELETE"
    }
  }

  container {
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest"
    
    # Add ML/AI environment variables and dependencies
    env {
      name  = "VERTEX_AI_ENDPOINT"
      value = "${var.location}-aiplatform.googleapis.com"
    }
    env {
      name  = "ENABLE_GPU_ACCELERATION"
      value = "true"
    }
  }

  host {
    gce_instance {
      machine_type      = var.ml_machine_type
      service_account   = google_service_account.workstation_sa.email
      boot_disk_size_gb = var.boot_disk_size_gb
      disable_public_ip = var.disable_public_ip
      
      # Correctly structured GPU configuration
      dynamic "accelerator" {
        for_each = var.enable_gpu ? [1] : []
        content {
          type  = var.gpu_type
          count = var.gpu_count
        }
      }
    }
  }
}

# Create workstation instances - optional, can be created on-demand through console
resource "google_workstations_workstation" "standard_workstation" {
  count = 0  # Set to 0 by default to avoid creating instances automatically
  
  workstation_id         = "standard-workstation"
  workstation_config_id  = google_workstations_workstation_config.standard_config.workstation_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  location               = var.location  # Added required location attribute
  
  labels = {
    "environment" = "development"
    "purpose"     = "orchestra-development"
  }
}

resource "google_workstations_workstation" "ml_workstation" {
  count = 0  # Set to 0 by default to avoid creating instances automatically
  
  workstation_id         = "ml-workstation"
  workstation_config_id  = google_workstations_workstation_config.ml_config.workstation_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  location               = var.location  # Added required location attribute
  
  labels = {
    "environment" = "development"
    "purpose"     = "orchestra-ml-development"
  }
}

# Outputs
output "workstation_cluster_id" {
  description = "The ID of the workstation cluster"
  value       = google_workstations_workstation_cluster.orchestra_cluster.id
}

output "standard_config_id" {
  description = "The ID of the standard workstation configuration"
  value       = google_workstations_workstation_config.standard_config.id
}

output "ml_config_id" {
  description = "The ID of the ML workstation configuration"
  value       = google_workstations_workstation_config.ml_config.id
}

output "connection_instructions" {
  description = "Instructions to connect to the workstation"
  value       = "Use the Google Cloud Console or gcloud CLI to start a workstation and connect to it."
}