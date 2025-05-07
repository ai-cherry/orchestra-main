# Terraform configuration for Cloud Workstations for Hybrid IDE setup
# This configuration supports the AGI Baby Cherry project (104944497835) with specific requirements
# for AI/ML and App/Infra development environments.

# ------------ Variables --------------
variable "workstation_cluster_name" {
  description = "Name for the Cloud Workstation cluster"
  type        = string
  default     = "hybrid-ide-cluster"
}

variable "workstation_config_name" {
  description = "Name for the Cloud Workstation configuration"
  type        = string
  default     = "hybrid-ide-config"
}

variable "workstation_name_prefix" {
  description = "Prefix for individual workstation names"
  type        = string
  default     = "hybrid-workstation"
}

variable "network_name" {
  description = "Name of the VPC network to use"
  type        = string
  default     = "default"
}

variable "gcs_bucket" {
  description = "GCS bucket to auto-mount for repository access"
  type        = string
  default     = "gs://cherry-ai-project-bucket/repos"
}

# ------------ Enable Required APIs --------------
resource "google_project_service" "workstation_apis" {
  for_each = toset([
    "workstations.googleapis.com",
    "compute.googleapis.com",
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# ------------ Cloud Workstation Cluster --------------
resource "google_workstations_workstation_cluster" "hybrid_cluster" {
  provider               = google-beta
  workstation_cluster_id = "${var.workstation_cluster_name}-${var.env}"
  network                = var.network_name
  subnetwork             = var.network_name
  location               = var.region
  project                = var.project_id

  # Labels for resource management
  labels = {
    env = var.env
  }

  # Private cluster configuration for security
  private_cluster_config {
    enable_private_endpoint = true
  }

  depends_on = [
    google_project_service.workstation_apis
  ]
}

# ------------ Cloud Workstation Configuration --------------
resource "google_workstations_workstation_config" "hybrid_config" {
  provider               = google-beta
  workstation_config_id  = "${var.workstation_config_name}-${var.env}"
  workstation_cluster_id = google_workstations_workstation_cluster.hybrid_cluster.workstation_cluster_id
  location               = var.region
  project                = var.project_id

  # Host configuration with GCE instance
  host {
    gce_instance {
      machine_type = "n2d-standard-32" # 32 vCPUs, AMD Milan optimized
      boot_disk_size_gb = 500        # Persistent 500GB SSD for agent memory
      accelerators {
        type  = "nvidia-tesla-t4"    # GPU for AI workloads
        count = 2                    # Increased to 2 GPUs for better performance
      }
      disable_public_ip_addresses = true
      shielded_instance_config {
        enable_secure_boot          = true
        enable_vtpm                 = true
        enable_integrity_monitoring = true
      }
    }
  }

  # Container configuration for preinstalled software
  container {
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/intellij-ultimate:latest"
    
    env = {
      "GEMINI_API_KEY"       = "AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
      "VERTEX_ENDPOINT"      = "projects/104944497835/locations/us-west4/endpoints/agent-core"
      "REDIS_CONNECTION"     = "redis://vertex-agent@cherry-ai-project"
    }
    
    # Custom startup script to install additional tools
    runtimes {
      name  = "install-additional-tools"
      type  = "SCRIPT"
      content = <<-EOF
        #!/bin/bash
        # Install JupyterLab
        pip3 install jupyterlab
        jupyter serverextension enable --py jupyterlab --sys-prefix
        
        # Set up Gemini Code Assist
        mkdir -p /home/user/
        cat > /home/user/.gemini-code-assist.yaml << 'GEMINICONFIG'
project_context:
  - path: /workspaces/orchestra-main
    priority: 100
  - path: /home/agent/mounted_bucket
    priority: 50

tool_integrations:
  vertex_ai:
    endpoint: projects/104944497835/locations/us-west4/endpoints/agent-core
    api_version: v1
  redis:
    connection_string: redis://vertex-agent@cherry-ai-project
GEMINICONFIG
      EOF
    }
  }

  # Enhanced persistent storage configuration
  persistent_directories {
    mount_path = "/home/agent/mounted_bucket"
    gce_pd {
      size_gb        = 1024  # 1TB persistent SSD
      fs_type        = "ext4"
      disk_type      = "pd-ssd"
      reclaim_policy = "DELETE"
    }
  }
  
  # Auto-mount GCS bucket for repository access
  persistent_directories {
    mount_path = "/mnt/repos"
    gce_pd {
      source      = var.gcs_bucket
      fs_type     = "gcsfuse"
      reclaim_policy = "DELETE"
    }
  }

  # Labels for resource management
  labels = {
    env = var.env
  }

  depends_on = [
    google_workstations_workstation_cluster.hybrid_cluster
  ]
}

# ------------ Cloud Workstation Instances --------------
resource "google_workstations_workstation" "hybrid_workstations" {
  provider               = google-beta
  count                  = 3  # Initial set of 3 workstations for pilot deployment
  workstation_id         = "${var.workstation_name_prefix}-${var.env}-${count.index + 1}"
  workstation_config_id  = google_workstations_workstation_config.hybrid_config.workstation_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.hybrid_cluster.workstation_cluster_id
  location               = var.region
  project                = var.project_id

  # Labels for resource management
  labels = {
    env = var.env
  }

  depends_on = [
    google_workstations_workstation_config.hybrid_config
  ]
}

# ------------ Service Account Permissions for Workstations --------------
resource "google_project_iam_member" "workstation_sa_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/compute.viewer",
    "roles/workstations.user"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:vertex-agent@cherry-ai-project.iam.gserviceaccount.com"
}

# ------------ Outputs --------------
output "workstation_details" {
  description = "Details of the provisioned Cloud Workstations"
  value = jsonencode({
    "cluster" = {
      "name"     = google_workstations_workstation_cluster.hybrid_cluster.workstation_cluster_id
      "location" = google_workstations_workstation_cluster.hybrid_cluster.location
    },
    "configuration" = {
      "name"          = google_workstations_workstation_config.hybrid_config.workstation_config_id
      "machine_type"  = google_workstations_workstation_config.hybrid_config.host[0].gce_instance[0].machine_type
      "disk_size"     = "${google_workstations_workstation_config.hybrid_config.host[0].gce_instance[0].boot_disk_size_gb} GB"
      "accelerator"   = google_workstations_workstation_config.hybrid_config.host[0].gce_instance[0].accelerators[0].type
      "mounted_bucket"= var.gcs_bucket
    },
    "workstations" = [
      for ws in google_workstations_workstation.hybrid_workstations : {
        "name" = ws.workstation_id
        "url"  = "https://${var.region}.workstations.cloud.google.com/${var.project_id}/${var.region}/${ws.workstation_cluster_id}/${ws.workstation_config_id}/${ws.workstation_id}"
      }
    ]
  })
}
