# Terraform configuration for Cloud Workstations with Vertex AI IDE integration
# For AI Orchestra Project (cherry-ai-project)

# ------------ Variables --------------
variable "workstation_cluster_name" {
  description = "Name for the Cloud Workstation cluster"
  type        = string
  default     = "ai-orchestra-cluster"
}

variable "workstation_config_name" {
  description = "Name for the Cloud Workstation configuration"
  type        = string
  default     = "ai-orchestra-config"
}

variable "workstation_name_prefix" {
  description = "Prefix for individual workstation names"
  type        = string
  default     = "ai-orchestra-workstation"
}

variable "network_name" {
  description = "Name of the VPC network to use"
  type        = string
  default     = "default"
}

variable "service_account_name" {
  description = "Service account name for the Cloud Workstation"
  type        = string
  default     = "vertex-ai-admin"
}

# ------------ Enable Required APIs --------------
resource "google_project_service" "workstation_apis" {
  for_each = toset([
    "workstations.googleapis.com",
    "compute.googleapis.com",
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "secretmanager.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# ------------ Service Account for Workstations --------------
resource "google_service_account" "workstation_sa" {
  account_id   = var.service_account_name
  display_name = "Vertex AI Workstation Service Account"
  description  = "Service account for Cloud Workstations with Vertex AI access"
  project      = var.project_id

  depends_on = [
    google_project_service.workstation_apis
  ]
}

# ------------ IAM Permissions for Workstation Service Account --------------
resource "google_project_iam_member" "workstation_sa_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/compute.viewer",
    "roles/workstations.user",
    "roles/secretmanager.secretAccessor"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.workstation_sa.email}"
}

# ------------ Cloud Workstation Cluster --------------
resource "google_workstations_workstation_cluster" "ai_orchestra_cluster" {
  provider               = google-beta
  workstation_cluster_id = "${var.workstation_cluster_name}-${var.env}"
  network                = var.network_name
  subnetwork             = var.network_name
  location               = var.region
  project                = var.project_id

  # Labels for resource management
  labels = {
    environment = var.env
    managed_by  = "terraform"
    project     = var.project_id
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
resource "google_workstations_workstation_config" "ai_orchestra_config" {
  provider               = google-beta
  workstation_config_id  = "${var.workstation_config_name}-${var.env}"
  workstation_cluster_id = google_workstations_workstation_cluster.ai_orchestra_cluster.workstation_cluster_id
  location               = var.region
  project                = var.project_id

  # Host configuration with GCE instance
  host {
    gce_instance {
      machine_type = "n2d-standard-16" # 16 vCPUs, AMD Milan optimized
      boot_disk_size_gb = 200        # Persistent 200GB SSD
      
      accelerators {
        type  = "nvidia-tesla-t4"    # GPU for AI workloads
        count = 1
      }
      
      disable_public_ip_addresses = true
      
      shielded_instance_config {
        enable_secure_boot          = true
        enable_vtpm                 = true
        enable_integrity_monitoring = true
      }
      
      service_account = google_service_account.workstation_sa.email
    }
  }

  # Container configuration for preinstalled software
  container {
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/intellij-ultimate:latest"
    
    env = {
      "VERTEX_ENDPOINT" = "projects/${var.project_id}/locations/${var.region}/endpoints/agent-core"
      "GCP_PROJECT_ID"  = var.project_id
      "JUPYTER_PORT"    = "8888"
    }
    
    # Custom startup script to install additional tools
    command = <<EOT
#!/bin/bash
set -e

echo "Setting up AI Orchestra development environment..."

# Install JupyterLab
echo "Installing JupyterLab..."
pip3 install jupyterlab ipywidgets pandas matplotlib scikit-learn tensorflow
jupyter serverextension enable --py jupyterlab --sys-prefix

# Install Vertex AI SDK
echo "Installing Vertex AI SDK..."
pip3 install google-cloud-aiplatform

# Install Gemini SDK
echo "Installing Gemini SDK..."
pip3 install google-generativeai

# Install Poetry
echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -

echo "AI Orchestra development environment setup complete!"
EOT
    # Set working directory in the command instead
    # Note: working_directory attribute is not supported in container block
  }

  # Note: Persistent storage is configured through the container
  # and host configuration instead of using persistent_directory
  # which is not supported in the current provider version

  labels = {
    environment = var.env
    managed_by  = "terraform"
    project     = var.project_id
  }

  depends_on = [
    google_workstations_workstation_cluster.ai_orchestra_cluster
  ]
}

# ------------ Cloud Workstation Instances --------------
resource "google_workstations_workstation" "ai_orchestra_workstations" {
  provider               = google-beta
  count                  = 2  # Initial set of 2 workstations
  workstation_id         = "${var.workstation_name_prefix}-${var.env}-${count.index + 1}"
  workstation_config_id  = google_workstations_workstation_config.ai_orchestra_config.workstation_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.ai_orchestra_cluster.workstation_cluster_id
  location               = var.region
  project                = var.project_id

  # Labels for resource management
  labels = {
    environment = var.env
    managed_by  = "terraform"
    project     = var.project_id
    instance    = "workstation-${count.index + 1}"
  }

  depends_on = [
    google_workstations_workstation_config.ai_orchestra_config
  ]
}

# ------------ Outputs --------------
output "workstation_details" {
  description = "Details of the provisioned Cloud Workstations"
  value = jsonencode({
    "cluster" = {
      "name"     = google_workstations_workstation_cluster.ai_orchestra_cluster.workstation_cluster_id
      "location" = google_workstations_workstation_cluster.ai_orchestra_cluster.location
    },
    "configuration" = {
      "name"          = google_workstations_workstation_config.ai_orchestra_config.workstation_config_id
      "machine_type"  = google_workstations_workstation_config.ai_orchestra_config.host[0].gce_instance[0].machine_type
      "disk_size"     = "${google_workstations_workstation_config.ai_orchestra_config.host[0].gce_instance[0].boot_disk_size_gb} GB"
      "accelerator"   = google_workstations_workstation_config.ai_orchestra_config.host[0].gce_instance[0].accelerators[0].type
    },
    "workstations" = [
      for ws in google_workstations_workstation.ai_orchestra_workstations : {
        "name" = ws.workstation_id
        "url"  = "https://${var.region}.workstations.cloud.google.com/${var.project_id}/${var.region}/${ws.workstation_cluster_id}/${ws.workstation_config_id}/${ws.workstation_id}"
      }
    ]
  })
}