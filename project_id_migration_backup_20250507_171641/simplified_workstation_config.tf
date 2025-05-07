# Simplified Terraform configuration for Cloud Workstations
# Based on the verified implementation for the agi-baby-cherry project

# Variables
variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "agi-baby-cherry"
}

variable "org_id" {
  description = "GCP organization ID"
  type        = string
  default     = "873291114285"
}

variable "gpu_type" {
  description = "GPU type for workstation"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "gpu_count" {
  description = "Number of GPUs"
  type        = number
  default     = 2
}

provider "google" {
  project = var.project_id
  region  = "us-central1"
}

resource "google_workstations_workstation_cluster" "ai_cluster" {
  workstation_cluster_id = "ai-development"
  network                = "default"
  subnetwork             = "default"
  location               = "us-central1"
}

resource "google_workstations_workstation_config" "ai_config" {
  workstation_config_id  = "ai-dev-config"
  workstation_cluster_id = google_workstations_workstation_cluster.ai_cluster.id
  location               = "us-central1"

  host {
    gce_instance {
      machine_type = "n2d-standard-32"
      accelerator {
        type  = var.gpu_type
        count = var.gpu_count
      }
      boot_disk_size_gb = 500
    }
  }

  persistent_directories {
    mount_path = "/home/ai"
    gce_pd {
      size_gb        = 1000
      fs_type        = "ext4"
      disk_type      = "pd-ssd"
      reclaim_policy = "RETAIN"
    }
  }
}

# Create workstation instances
resource "google_workstations_workstation" "ai_workstations" {
  count                  = 3
  workstation_id         = "ai-workstation-${count.index + 1}"
  workstation_config_id  = google_workstations_workstation_config.ai_config.workstation_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.ai_cluster.workstation_cluster_id
  location               = "us-central1"
}

# Output workstation URLs
output "workstation_urls" {
  value = [
    for ws in google_workstations_workstation.ai_workstations :
    "https://us-central1.workstations.cloud.goog/${var.project_id}/us-central1/${ws.workstation_cluster_id}/${ws.workstation_config_id}/${ws.workstation_id}"
  ]
}

# Output verification info for checking migration success
output "verification_info" {
  value = {
    organization_id  = var.org_id
    project_id       = var.project_id
    workstation_info = {
      cluster        = "ai-development"
      config         = "ai-dev-config"
      machine_type   = "n2d-standard-32"
      gpu_type       = var.gpu_type
      gpu_count      = var.gpu_count
    }
  }
}
