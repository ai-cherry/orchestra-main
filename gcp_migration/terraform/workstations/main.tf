/**
 * GCP Workstations Terraform module
 * 
 * This module creates GCP Workstations for the AI Orchestra project,
 * including standard and ML-optimized configurations.
 */

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.40.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 4.40.0"
    }
  }
  backend "gcs" {
    # Configured via backend-config in terraform init
  }
}

provider "google" {
  project = var.project_id
  region  = var.location
}

provider "google-beta" {
  project = var.project_id
  region  = var.location
}

#-----------------------------
# Local variables
#-----------------------------
locals {
  resource_prefix    = "orchestra-${var.env}"
  private_ip_ranges  = var.enable_public_ip ? [] : ["0.0.0.0/0"]
  service_account_id = "${local.resource_prefix}-sa"
  labels             = merge(var.labels, {
    "environment" = var.env
  })
}

#-----------------------------
# Network resources
#-----------------------------
resource "google_compute_network" "workstation_network" {
  name                    = var.network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "workstation_subnet" {
  name          = var.subnet_name
  ip_cidr_range = var.subnet_cidr
  region        = var.location
  network       = google_compute_network.workstation_network.id
  
  # Enable Private Google Access for accessing GCP APIs without external IP
  private_ip_google_access = true
  
  # Optional: Configure flow logs for network monitoring
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Create a firewall rule to allow connections to workstations
resource "google_compute_firewall" "allow_workstation_access" {
  name    = "${local.resource_prefix}-allow-workstation"
  network = google_compute_network.workstation_network.id
  
  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443", "3389", "8080"]
  }
  
  target_tags   = ["workstation"]
  source_ranges = var.allowed_cidrs
}

# Create a router and NAT for internet access from private instances
resource "google_compute_router" "workstation_router" {
  name    = "${local.resource_prefix}-router"
  region  = var.location
  network = google_compute_network.workstation_network.id
}

resource "google_compute_router_nat" "workstation_nat" {
  name                               = "${local.resource_prefix}-nat"
  router                             = google_compute_router.workstation_router.name
  region                             = var.location
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

#-----------------------------
# Service account
#-----------------------------
resource "google_service_account" "workstation_sa" {
  account_id   = local.service_account_id
  display_name = "Workstation Service Account for ${var.env}"
  description  = "Service account for AI Orchestra workstations"
}

# Assign roles to the service account
resource "google_project_iam_member" "workstation_sa_roles" {
  for_each = toset(var.service_account_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.workstation_sa.email}"
}

#-----------------------------
# Workstation cluster
#-----------------------------
resource "google_workstations_workstation_cluster" "orchestra_cluster" {
  provider = google-beta
  
  workstation_cluster_id = var.workstation_cluster_id
  display_name           = "AI Orchestra Workstation Cluster (${var.env})"
  location               = var.location
  network                = google_compute_network.workstation_network.id
  subnetwork             = google_compute_subnetwork.workstation_subnet.id
  
  labels                 = local.labels
  
  # Private cluster configuration
  private_cluster_config {
    enable_private_endpoint = !var.enable_public_ip
    allowed_projects        = [var.project_id]
  }
}

#-----------------------------
# Standard workstation configuration
#-----------------------------
resource "google_workstations_workstation_config" "standard_config" {
  provider = google-beta
  
  workstation_config_id  = var.standard_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  display_name           = "Standard Configuration"
  location               = var.location
  
  container {
    image = var.standard_container_image
    
    # Container environment variables (using env map)
    env = {
      "PROJECT_ID"  = var.project_id
      "ENVIRONMENT" = var.env
    }
    
    # Container command for startup
    command = ["/entrypoint.sh"]
  }
  
  # Persistent directories
  persistent_directories {
    mount_path = "/home/user/persistent"
    gce_pd {
      size_gb        = var.persistent_disk_size_gb
      reclaim_policy = "DELETE"
      disk_type      = "pd-balanced"
    }
  }
  
  # Host VM configuration
  host {
    gce_instance {
      machine_type      = var.standard_machine_type
      service_account   = google_service_account.workstation_sa.email
      boot_disk_size_gb = var.boot_disk_size_gb
      tags              = ["workstation"]
      
      # Shielded instance config
      shielded_instance_config {
        enable_secure_boot          = var.enable_secure_boot
        enable_vtpm                 = true
        enable_integrity_monitoring = true
      }
    }
  }
  
  # Timeouts
  timeouts {
    create = "20m"
    update = "20m"
    delete = "20m"
  }
  
  # Idle/running timeouts
  idle_timeout   = var.enable_auto_suspend ? "${var.idle_timeout_minutes}m" : null
  running_timeout = "${var.running_timeout_minutes}m"
  
  # Additional labels
  labels = local.labels
}

#-----------------------------
# ML workstation configuration with GPU support
#-----------------------------
# Note: When using GPU, the container image must support NVIDIA GPUs
# and the appropriate drivers will be installed based on machine type
resource "google_workstations_workstation_config" "ml_config" {
  provider = google-beta
  count    = var.enable_gpu ? 1 : 0
  
  workstation_config_id  = var.ml_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  display_name           = "ML Configuration with GPU"
  location               = var.location
  
  container {
    image = var.ml_container_image
    
    # Container environment variables (using env map)
    env = {
      "PROJECT_ID"          = var.project_id
      "ENVIRONMENT"         = var.env
      "CUDA_VISIBLE_DEVICES" = "0"
    }
    
    # Container commands for GPU setup
    command = [
      "/bin/bash",
      "-c",
      "nvidia-smi && echo 'GPU is available' && /entrypoint.sh"
    ]
  }
  
  # Persistent directories
  persistent_directories {
    mount_path = "/home/user/persistent"
    gce_pd {
      size_gb        = var.persistent_disk_size_gb
      reclaim_policy = "DELETE"
      disk_type      = "pd-ssd"  # SSD for ML workloads
    }
  }
  
  # Host VM configuration
  host {
    gce_instance {
      # Use a GPU-enabled machine type (e.g., n1-standard-8)
      # GPU type will be determined based on the machine family
      machine_type      = var.ml_machine_type
      service_account   = google_service_account.workstation_sa.email
      boot_disk_size_gb = var.boot_disk_size_gb
      tags              = ["workstation", "gpu"]
      
      # Shielded instance config
      shielded_instance_config {
        enable_secure_boot          = var.enable_secure_boot
        enable_vtpm                 = true
        enable_integrity_monitoring = true
      }
    }
  }
  
  # Timeouts
  timeouts {
    create = "20m"
    update = "20m"
    delete = "20m"
  }
  
  # Idle/running timeouts
  idle_timeout   = var.enable_auto_suspend ? "${var.idle_timeout_minutes}m" : null
  running_timeout = "${var.running_timeout_minutes}m"
  
  # Additional labels
  labels = merge(local.labels, {
    "gpu-enabled" = "true"
  })
  
  # Note: GPU configuration will be handled by choosing an appropriate 
  # machine type and container image. The workstation service will
  # automatically provision the necessary GPU drivers.
}

#-----------------------------
# Example workstation instance
#-----------------------------
resource "google_workstations_workstation" "example_workstation" {
  provider = google-beta
  
  workstation_id         = "example-workstation"
  workstation_config_id  = google_workstations_workstation_config.standard_config.workstation_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  location               = var.location
  
  labels = local.labels
}

#-----------------------------
# Outputs
#-----------------------------
output "workstation_cluster_id" {
  description = "The ID of the workstation cluster"
  value       = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
}

output "standard_config_id" {
  description = "The ID of the standard workstation configuration"
  value       = google_workstations_workstation_config.standard_config.workstation_config_id
}

output "ml_config_id" {
  description = "The ID of the ML workstation configuration"
  value       = var.enable_gpu ? google_workstations_workstation_config.ml_config[0].workstation_config_id : "GPU configuration not enabled"
}

output "example_workstation_id" {
  description = "The ID of the example workstation"
  value       = google_workstations_workstation.example_workstation.workstation_id
}

output "workstation_service_account" {
  description = "The service account used by workstations"
  value       = google_service_account.workstation_sa.email
}

output "network_name" {
  description = "The name of the VPC network"
  value       = google_compute_network.workstation_network.name
}

output "subnet_name" {
  description = "The name of the subnet"
  value       = google_compute_subnetwork.workstation_subnet.name
}

output "example_workstation_url" {
  description = "URL to access the example workstation (if public IPs are enabled)"
  value       = var.enable_public_ip ? "https://console.cloud.google.com/workstations/instances/${var.location}/${google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id}/${google_workstations_workstation.example_workstation.workstation_id}?project=${var.project_id}" : "Workstation has no public IP"
}