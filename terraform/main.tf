# Performance-optimized Terraform configuration for GCP Workstations
# Main infrastructure deployment for GitHub Codespaces to GCP Workstations migration

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.50.0"
    }
  }
  
  # Uncomment to use a GCS backend for state management
  # backend "gcs" {
  #   bucket  = "terraform-state-BUCKET_NAME"
  #   prefix  = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Local variables for configuration
locals {
  network_name     = "${var.project_prefix}-network"
  subnet_name      = "${var.project_prefix}-subnet"
  router_name      = "${var.project_prefix}-router"
  cluster_name     = "${var.project_prefix}-cluster"
  service_account  = "${var.project_prefix}-workstation-sa"
}

# Create dedicated service account for workstations
resource "google_service_account" "workstation_sa" {
  account_id   = local.service_account
  display_name = "Workstation Service Account"
  description  = "Service account for GCP Cloud Workstations with performance-optimized permissions"
}

# Apply roles to service account (simplified for performance)
resource "google_project_iam_member" "workstation_roles" {
  for_each = toset(var.service_account_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.workstation_sa.email}"
}

# VPC network for workstations
resource "google_compute_network" "workstation_network" {
  name                    = local.network_name
  auto_create_subnetworks = false
  description             = "Network for GCP Cloud Workstations"
}

# Subnet for workstations
resource "google_compute_subnetwork" "workstation_subnet" {
  name          = local.subnet_name
  ip_cidr_range = var.ip_cidr_range
  region        = var.region
  network       = google_compute_network.workstation_network.id
  
  # Enable Google private access for better service connectivity
  private_ip_google_access = true
  
  # Enable VPC flow logs for improved monitoring
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Router for outbound connectivity
resource "google_compute_router" "router" {
  name    = local.router_name
  region  = var.region
  network = google_compute_network.workstation_network.id
}

# NAT gateway for outbound connectivity without public IPs
resource "google_compute_router_nat" "nat" {
  name                               = "${var.project_prefix}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  # Performance-optimized NAT configuration
  tcp_established_idle_timeout_sec = 1200
  udp_idle_timeout_sec             = 30
  
  log_config {
    enable = var.enable_monitoring
    filter = "ERRORS_ONLY"
  }
}

# Cloud Workstations cluster
resource "google_workstations_workstation_cluster" "cluster" {
  workstation_cluster_id = local.cluster_name
  network                = google_compute_network.workstation_network.id
  subnetwork             = google_compute_subnetwork.workstation_subnet.id
  
  private_cluster_config {
    enable_private_endpoint = false
  }
  
  # Performance-optimized config
  maintenance_policy {
    maintenance_window {
      day_of_week = "SATURDAY"
      start_time {
        hours   = 1
        minutes = 0
        seconds = 0
      }
    }
  }
}

# Standard development workstation configuration
resource "google_workstations_workstation_config" "standard_config" {
  workstation_config_id     = "${var.project_prefix}-standard-config"
  workstation_cluster_id    = google_workstations_workstation_cluster.cluster.workstation_cluster_id
  display_name              = "Standard Development Configuration"
  
  # Persistent disk for repository storage
  persistent_directories {
    mount_path = "/home/user/persistent"
    gcePd {
      size_gb        = var.persistent_disk_size_gb
      reclaim_policy = "DELETE"
      
      # Performance-optimized disk type
      disk_type      = "pd-ssd"
    }
  }
  
  # Container configuration
  container {
    image = var.container_image
    
    # Common environment variables
    dynamic "env" {
      for_each = var.environment_variables
      content {
        name  = env.key
        value = env.value
      }
    }
    
    # Performance optimizations
    env {
      name  = "NODE_OPTIONS"
      value = "--max-old-space-size=8192"
    }
    
    env {
      name  = "PYTHONUNBUFFERED"
      value = "1"
    }
    
    env {
      name  = "DISABLE_TELEMETRY"
      value = "true"
    }
    
    # Startup command with optimized settings
    command = "code --user-data-dir=/home/user/persistent/.vscode-server --disable-gpu --disable-software-rasterizer --disable-telemetry"
  }
  
  # VM configuration
  host {
    gce_instance {
      machine_type      = var.standard_machine_type
      service_account   = google_service_account.workstation_sa.email
      boot_disk_size_gb = var.boot_disk_size_gb
      disable_public_ip = var.disable_public_ip
      
      # Performance-optimized configuration
      shielded_instance_config {
        enable_secure_boot          = false  # Disable for performance
        enable_vtpm                 = false  # Disable for performance
        enable_integrity_monitoring = false  # Disable for performance
      }
    }
  }
  
  # Automatic shutdown for cost optimization
  idle_timeout {
    idle_timeout_minutes = var.auto_shutdown_minutes
  }
}

# ML-optimized workstation configuration
resource "google_workstations_workstation_config" "ml_config" {
  count                  = var.enable_gpu ? 1 : 0
  workstation_config_id  = "${var.project_prefix}-ml-config"
  workstation_cluster_id = google_workstations_workstation_cluster.cluster.workstation_cluster_id
  display_name           = "ML-Optimized Configuration with GPU"
  
  # Persistent disk for repository and ML model storage
  persistent_directories {
    mount_path = "/home/user/persistent"
    gcePd {
      size_gb        = var.persistent_disk_size_gb
      reclaim_policy = "DELETE"
      
      # Performance-optimized disk type
      disk_type      = "pd-ssd"
    }
  }
  
  # Container configuration for ML workloads
  container {
    image = var.container_image
    
    # Common environment variables
    dynamic "env" {
      for_each = var.environment_variables
      content {
        name  = env.key
        value = env.value
      }
    }
    
    # ML-specific environment variables
    env {
      name  = "CUDA_VISIBLE_DEVICES"
      value = "0"
    }
    
    env {
      name  = "NVIDIA_DRIVER_CAPABILITIES"
      value = "compute,utility"
    }
    
    env {
      name  = "NVIDIA_VISIBLE_DEVICES"
      value = "all"
    }
    
    env {
      name  = "VERTEX_AI_ENDPOINT"
      value = "${var.region}-aiplatform.googleapis.com"
    }
    
    # Startup command with optimized settings
    command = "code --user-data-dir=/home/user/persistent/.vscode-server --disable-gpu --disable-software-rasterizer --disable-telemetry"
  }
  
  # VM configuration with GPU
  host {
    gce_instance {
      machine_type      = var.ml_machine_type
      service_account   = google_service_account.workstation_sa.email
      boot_disk_size_gb = var.boot_disk_size_gb
      disable_public_ip = var.disable_public_ip
      
      # GPU configuration
      accelerator_count = var.gpu_count
      accelerator_type  = var.gpu_type
      
      # Performance-optimized configuration
      shielded_instance_config {
        enable_secure_boot          = false  # Disable for performance
        enable_vtpm                 = false  # Disable for performance
        enable_integrity_monitoring = false  # Disable for performance
      }
    }
  }
  
  # Automatic shutdown for cost optimization
  idle_timeout {
    idle_timeout_minutes = var.auto_shutdown_minutes
  }
}

# Output the endpoint URLs
output "workstation_cluster_endpoint" {
  value       = google_workstations_workstation_cluster.cluster.name
  description = "The name of the Cloud Workstations cluster"
}

output "standard_config_name" {
  value       = google_workstations_workstation_config.standard_config.name
  description = "The name of the standard workstation configuration"
}

output "ml_config_name" {
  value       = var.enable_gpu ? google_workstations_workstation_config.ml_config[0].name : "GPU disabled"
  description = "The name of the ML-optimized workstation configuration"
}

output "service_account" {
  value       = google_service_account.workstation_sa.email
  description = "Service account email for the workstations"
}