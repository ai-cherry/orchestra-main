# GCP Cloud Workstation Module
# 
# This module provisions a Cloud Workstation environment for AI development with:
#  - n2d-standard-32 machine type
#  - 2x NVIDIA T4 GPUs
#  - 1TB persistent SSD
#  - Preinstalled JupyterLab and IntelliJ

# Enable required APIs
resource "google_project_service" "workstation_apis" {
  for_each = toset([
    "workstations.googleapis.com",
    "compute.googleapis.com",
    "aiplatform.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Cloud Workstation Cluster
resource "google_workstations_workstation_cluster" "ai_cluster" {
  provider               = google-beta
  project                = var.project_id
  region                 = var.region
  workstation_cluster_id = var.cluster_name
  network                = var.network_name
  subnetwork             = var.subnetwork_name
  
  private_cluster_config {
    enable_private_endpoint = var.private_endpoint_enabled
  }
  
  depends_on = [google_project_service.workstation_apis]
}

# Cloud Workstation Configuration
resource "google_workstations_workstation_config" "ai_config" {
  provider               = google-beta
  project                = var.project_id
  region                 = var.region
  workstation_cluster_id = google_workstations_workstation_cluster.ai_cluster.workstation_cluster_id
  workstation_config_id  = var.config_name

  # Host configuration
  host {
    gce_instance {
      machine_type = "n2d-standard-32"
      
      # NVIDIA T4 GPUs
      accelerator {
        type  = "nvidia-tesla-t4"
        count = 2
      }
      
      # Boot disk configuration
      boot_disk_size_gb = 100
      
      # Enhanced security options
      shielded_instance_config {
        enable_secure_boot          = true
        enable_vtpm                 = true
        enable_integrity_monitoring = true
      }
      
      # Private networking configuration (optional)
      disable_public_ip_addresses = var.disable_public_ip
    }
  }

  # 1TB Persistent SSD storage
  persistent_directories {
    mount_path = "/home/user/persistent-data"
    gce_pd {
      size_gb        = 1024  # 1TB
      disk_type      = "pd-ssd"
      reclaim_policy = "DELETE"
    }
  }

  # Container configuration with preinstalled tools
  container {
    # Use the official IntelliJ IDE image from Google
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/intellij-ultimate:latest"
    
    # Environment variables
    env = var.environment_variables
    
    # Install JupyterLab
    runtime {
      args = ["bash", "-c", "pip install jupyterlab && jupyter labextension install @jupyter-widgets/jupyterlab-manager && mkdir -p ~/.jupyter"]
    }

    # Custom startup script to setup environment
    runnable {
      type    = "script"
      content = <<-EOT
#!/bin/bash
# Install additional tools and configure environment
pip install --user jupyterlab numpy pandas tensorflow matplotlib scikit-learn
jupyter lab --generate-config
echo "c.ServerApp.ip = '0.0.0.0'" >> ~/.jupyter/jupyter_lab_config.py
echo "c.ServerApp.allow_origin = '*'" >> ~/.jupyter/jupyter_lab_config.py

# Create startup script for JupyterLab
cat > ~/start_jupyter.sh << 'EOF'
#!/bin/bash
jupyter lab --no-browser --port=8888 --ip=0.0.0.0
EOF
chmod +x ~/start_jupyter.sh

# Notify user
echo "==================================================="
echo "Cloud Workstation setup complete!"
echo "JupyterLab available at: http://localhost:8888"
echo "Run ~/start_jupyter.sh to start JupyterLab"
echo "==================================================="
EOT
    }
  }

  depends_on = [google_workstations_workstation_cluster.ai_cluster]
}

# Workstation instance
resource "google_workstations_workstation" "ai_workstation" {
  provider               = google-beta
  project                = var.project_id
  region                 = var.region
  workstation_cluster_id = google_workstations_workstation_cluster.ai_cluster.workstation_cluster_id
  workstation_config_id  = google_workstations_workstation_config.ai_config.workstation_config_id
  workstation_id         = var.workstation_name

  depends_on = [google_workstations_workstation_config.ai_config]
}

# IAM binding for service account
resource "google_project_iam_binding" "workstation_iam" {
  project = var.project_id
  role    = "roles/workstations.user"
  
  members = [
    "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
  ]
}

# Additional IAM role for AI platform
resource "google_project_iam_binding" "ai_platform_iam" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  
  members = [
    "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
  ]
}
