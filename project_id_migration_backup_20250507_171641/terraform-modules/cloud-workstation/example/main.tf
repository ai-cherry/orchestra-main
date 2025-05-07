# Example usage of the Cloud Workstation Module

provider "google" {
  project = "agi-baby-cherry"
  region  = "us-central1"
}

provider "google-beta" {
  project = "agi-baby-cherry"
  region  = "us-central1"
}

module "ai_workstation" {
  source = "../"  # Path to the cloud-workstation module

  # Project configuration
  project_id = "agi-baby-cherry"
  region     = "us-central1"
  
  # Workstation naming
  cluster_name     = "ai-development"
  config_name      = "ai-dev-config"
  workstation_name = "ai-workstation-1"
  
  # Hardware configuration
  machine_type          = "n2d-standard-32"
  gpu_type              = "nvidia-tesla-t4"
  gpu_count             = 2
  persistent_disk_size_gb = 1024
  
  # Network configuration
  network_name    = "default"
  subnetwork_name = "default"
  disable_public_ip = false
  
  # Environment variables
  environment_variables = {
    "JUPYTER_PORT"     = "8888",
    "VERTEX_PROJECT"   = "agi-baby-cherry",
    "VERTEX_LOCATION"  = "us-central1",
    "NOTEBOOK_DIR"     = "/home/user/persistent-data/notebooks"
  }
  
  # Tags for resource management
  tags = {
    "environment" = "development",
    "purpose"     = "ai-development",
    "project"     = "agi-baby-cherry"
  }
}

# Output the connection information
output "workstation_url" {
  description = "URL to access the workstation"
  value       = module.ai_workstation.workstation_url
}

output "workstation_ip" {
  description = "External IP of the workstation (if public IP is enabled)"
  value       = module.ai_workstation.workstation_ip
}

output "connection_command" {
  description = "Command to start and connect to the workstation"
  value       = module.ai_workstation.workstation_connection_command
}

output "jupyter_command" {
  description = "Command to connect to JupyterLab"
  value       = module.ai_workstation.jupyter_connection_command
}

output "machine_specs" {
  description = "Hardware specifications of the workstation"
  value       = module.ai_workstation.machine_specs
}
