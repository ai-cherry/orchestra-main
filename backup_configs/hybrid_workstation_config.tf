# Terraform configuration for Cloud Workstations with optimal AI development settings
# For AGI Baby Cherry Project (104944497835)
# 
# This configuration sets up:
# - Cloud Workstations with JupyterLab + IntelliJ
# - Optimal machine configuration for AI development
# - Redis/AlloyDB memory layer integration
# - Gemini Code Assist integration

# ------------ Variables --------------
variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "project_number" {
  description = "The Google Cloud project number"
  type        = string
  default     = "104944497835"
}

variable "region" {
  description = "The Google Cloud region to deploy resources"
  type        = string
  default     = "us-west4"
}

variable "zone" {
  description = "The Google Cloud zone within the region"
  type        = string
  default     = "us-west4-a"
}

variable "service_account_email" {
  description = "Service account email for the Cloud Workstation"
  type        = string
  default     = "vertex-agent@cherry-ai-project.iam.gserviceaccount.com"
}

variable "admin_email" {
  description = "Admin email for notifications and ownership"
  type        = string
  default     = "scoobyjava@cherry-ai.me"
}

variable "gemini_api_key" {
  description = "API key for Gemini Code Assist"
  type        = string
  default     = "AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "gcs_bucket" {
  description = "GCS bucket to auto-mount for repository access"
  type        = string
  default     = "gs://cherry-ai-project-bucket/repos"
}

# ------------ Provider Configuration --------------
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ------------ Enable Required APIs --------------
resource "google_project_service" "required_apis" {
  for_each = toset([
    "workstations.googleapis.com",
    "compute.googleapis.com",
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "redis.googleapis.com",
    "alloydb.googleapis.com",
    "bigquery.googleapis.com",
    "monitoring.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# ------------ Cloud Workstation Cluster --------------
resource "google_workstations_workstation_cluster" "hybrid_cluster" {
  provider               = google-beta
  workstation_cluster_id = "hybrid-ide-cluster-${var.env}"
  network                = "default"
  subnetwork             = "default"
  location               = var.region
  project                = var.project_id

  # Network configurations for security
  private_cluster_config {
    enable_private_endpoint = true
  }

  # Labels for resource management
  labels = {
    env        = var.env
    managed_by = "terraform"
    project    = "cherry-ai-project"
    org        = "cherry-ai"
  }

  depends_on = [
    google_project_service.required_apis
  ]
}

# ------------ Cloud Workstation Configuration for AI Development --------------
resource "google_workstations_workstation_config" "hybrid_config" {
  provider               = google-beta
  workstation_config_id  = "hybrid-ide-config-${var.env}"
  workstation_cluster_id = google_workstations_workstation_cluster.hybrid_cluster.workstation_cluster_id
  location               = var.region
  project                = var.project_id

  # Host configuration with optimized compute resources for AI development
  host {
    gce_instance {
      # n2d-standard-32 with AMD Milan for optimal performance
      machine_type = "n2d-standard-32"
      
      # 500GB SSD for agent memory and large datasets
      boot_disk_size_gb = 500
      
      # GPU configuration for AI/ML workloads
      accelerators {
        type  = "nvidia-tesla-t4"
        count = 2
      }
      
      # Security configurations
      disable_public_ip_addresses = true
      shielded_instance_config {
        enable_secure_boot          = true
        enable_vtpm                 = true
        enable_integrity_monitoring = true
      }
      
      # Use custom service account
      service_account = var.service_account_email
      
      # Enable confidential computing for sensitive AI models
      confidential_instance_config {
        enable_confidential_compute = true
      }
      
      # Performance optimization for AI workloads
      performance_monitoring_unit = "PERFORMANCE_MONITORING_UNIT_ENABLED"
      
      # Network tags for firewall rules
      tags = ["hybrid-ide", "ai-development", "cherry-ai"]
    }
  }

  # Container configuration with IntelliJ and JupyterLab
  container {
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/intellij-ultimate:latest"
    
    # Environment variables for Gemini, Vertex AI, and Redis
    env = {
      "GEMINI_API_KEY"       = var.gemini_api_key
      "VERTEX_ENDPOINT"      = "projects/${var.project_number}/locations/${var.region}/endpoints/agent-core"
      "REDIS_CONNECTION"     = "redis://vertex-agent@${var.project_id}"
      "ALLOYDB_CONNECTION"   = "postgresql://alloydb-user@alloydb-instance:5432/agi_baby_cherry"
      "GCP_PROJECT_ID"       = var.project_id
      "GCP_PROJECT_NUMBER"   = var.project_number
      "JUPYTER_PORT"         = "8888"
    }
    
    # Custom startup script to install and configure JupyterLab and other tools
    runtimes {
      name  = "install-ide-components"
      type  = "SCRIPT"
      content = <<-EOF
        #!/bin/bash
        set -e
        
        echo "Setting up hybrid IDE environment..."
        
        # Install JupyterLab
        echo "Installing JupyterLab..."
        pip3 install jupyterlab ipywidgets pandas matplotlib scikit-learn tensorflow
        jupyter serverextension enable --py jupyterlab --sys-prefix
        
        # Install AlloyDB Connector
        echo "Installing AlloyDB connector..."
        pip3 install sqlalchemy psycopg2-binary google-cloud-alloydb
        
        # Install Redis client
        echo "Installing Redis client..."
        pip3 install redis hiredis redis-om
        
        # Install Gemini SDK
        echo "Installing Gemini SDK..."
        pip3 install google-generativeai vertexai
        
        # Set up Gemini Code Assist
        echo "Setting up Gemini Code Assist..."
        mkdir -p /home/user/
        cat > /home/user/.gemini-code-assist.yaml << 'GEMINICONFIG'
project_context:
  - path: /workspaces/orchestra-main
    priority: 100
  - path: /home/agent/mounted_bucket
    priority: 50
  - path: /mnt/repos
    priority: 25

tool_integrations:
  vertex_ai:
    endpoint: projects/${var.project_number}/locations/${var.region}/endpoints/agent-core
    api_version: v1
  redis:
    connection_string: redis://vertex-agent@${var.project_id}
  database:
    connection_string: postgresql://alloydb-user@alloydb-instance:5432/agi_baby_cherry

model:
  name: gemini-2.5
  temperature: 0.3
  max_output_tokens: 8192
  top_p: 0.95
GEMINICONFIG
        
        # Create JupyterLab startup script
        echo "Creating JupyterLab startup script..."
        cat > /home/user/start_jupyter.sh << 'JUPYTERSCRIPT'
#!/bin/bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --ServerApp.token='' --ServerApp.password=''
JUPYTERSCRIPT
        chmod +x /home/user/start_jupyter.sh
        
        # Create environment check script
        echo "Creating environment check script..."
        cat > /home/user/check_environment.py << 'CHECKENV'
#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def check_component(name, check_command):
    print(f"Checking {name}...")
    try:
        subprocess.run(check_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ {name} is properly configured")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {name} is NOT properly configured")
        return False

def main():
    print("===== Hybrid IDE Environment Check =====")
    print(f"Python version: {platform.python_version()}")
    
    # Check JupyterLab
    check_component("JupyterLab", "jupyter --version")
    
    # Check Redis connection
    redis_conn = os.environ.get("REDIS_CONNECTION", "")
    if redis_conn:
        check_component("Redis", "python -c 'import redis; r=redis.from_url(\"" + redis_conn + "\"); r.ping()'")
    
    # Check AlloyDB connection
    alloydb_conn = os.environ.get("ALLOYDB_CONNECTION", "")
    if alloydb_conn:
        check_component("AlloyDB", "python -c 'import psycopg2; conn=psycopg2.connect(\"" + alloydb_conn + "\")'")
    
    # Check Gemini API
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        check_component("Gemini API", "python -c 'import google.generativeai as genai; genai.configure(api_key=\"" + gemini_key + "\")'")
    
    print("===== Environment Check Complete =====")

if __name__ == "__main__":
    main()
CHECKENV
        chmod +x /home/user/check_environment.py
        
        echo "Hybrid IDE environment setup complete!"
      EOF
    }
    
    # Working directory configuration
    working_directory = "/home/user"
    
    # Mount additional volumes
    volumes {
      mount_path = "/home/user/.m2"
      name       = "maven-cache"
    }
    
    volumes {
      mount_path = "/home/user/.gradle"
      name       = "gradle-cache"
    }
  }

  # Persistent storage for agent memory
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
      source          = var.gcs_bucket
      fs_type         = "gcsfuse"
      reclaim_policy  = "DELETE"
    }
  }

  # Dedicated cache volume for faster builds
  persistent_directories {
    mount_path = "/home/user/.cache"
    gce_pd {
      size_gb        = 100
      fs_type        = "ext4"
      disk_type      = "pd-ssd"
      reclaim_policy = "DELETE"
    }
  }

  # Labels for resource management
  labels = {
    env        = var.env
    managed_by = "terraform"
    project    = "cherry-ai-project"
    org        = "cherry-ai"
  }

  depends_on = [
    google_workstations_workstation_cluster.hybrid_cluster
  ]
}

# ------------ Cloud Workstation Instances --------------
resource "google_workstations_workstation" "hybrid_workstations" {
  provider               = google-beta
  count                  = 3  # Initial set of 3 workstations for development team
  workstation_id         = "hybrid-workstation-${var.env}-${count.index + 1}"
  workstation_config_id  = google_workstations_workstation_config.hybrid_config.workstation_config_id
  workstation_cluster_id = google_workstations_workstation_cluster.hybrid_cluster.workstation_cluster_id
  location               = var.region
  project                = var.project_id

  # Labels for resource management
  labels = {
    env        = var.env
    managed_by = "terraform"
    project    = "cherry-ai-project"
    org        = "cherry-ai"
    instance   = "workstation-${count.index + 1}"
  }

  depends_on = [
    google_workstations_workstation_config.hybrid_config
  ]
}

# ------------ IAM Permissions for Workstations --------------
resource "google_project_iam_member" "workstation_sa_permissions" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/compute.viewer",
    "roles/workstations.user",
    "roles/redis.viewer",
    "roles/alloydb.viewer",
    "roles/bigquery.dataViewer",
    "roles/monitoring.viewer"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${var.service_account_email}"
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
