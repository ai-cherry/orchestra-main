# simplified_deployment.tf - Streamlined Terraform configuration for single-developer projects
# Prioritizes development velocity and simplicity over complex security measures

# Provider configuration with simplified authentication
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Variables with sensible defaults
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "service_name" {
  description = "Name of the service"
  type        = string
  default     = "ai-orchestra"
}

variable "env" {
  description = "Environment (dev, prod)"
  type        = string
  default     = "dev"
}

# Simplified Cloud Run service
resource "google_cloud_run_service" "app" {
  name     = "${var.service_name}-${var.env}"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/${var.service_name}:latest"
        
        # Direct environment variables instead of secrets for simplicity
        env {
          name  = "ENV"
          value = var.env
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  # Skip waiting for service to be ready for faster deployment
  autogenerate_revision_name = true
  
  # Simple traffic configuration
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Public access for easy development
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.app.name
  location = google_cloud_run_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"  # Public access for easy testing
}

# Simple Firestore database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  # Simplified settings for development
}

# Simple Cloud Storage bucket
resource "google_storage_bucket" "storage" {
  name          = "${var.project_id}-${var.service_name}-${var.env}"
  location      = var.region
  force_destroy = true  # Allow easy cleanup

  # Simplified settings for development
  uniform_bucket_level_access = true
  
  # Public access for easy development
  public_access_prevention = "inherited"
}

# Simple service account with broad permissions for development
resource "google_service_account" "service_account" {
  account_id   = "${var.service_name}-${var.env}"
  display_name = "${var.service_name} Service Account (${var.env})"
}

# Broad permissions for development velocity
resource "google_project_iam_member" "service_account_roles" {
  for_each = toset([
    "roles/datastore.user",
    "roles/storage.admin",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.service_account.email}"
}

# Bind service account to Cloud Run service
resource "google_cloud_run_service_iam_member" "service_account_binding" {
  service  = google_cloud_run_service.app.name
  location = google_cloud_run_service.app.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.service_account.email}"
}

# Output important information
output "service_url" {
  value = google_cloud_run_service.app.status[0].url
}

output "service_account_email" {
  value = google_service_account.service_account.email
}

output "bucket_name" {
  value = google_storage_bucket.storage.name
}

output "firestore_database" {
  value = google_firestore_database.database.name
}

# Simplified deployment script
resource "local_file" "deploy_script" {
  filename = "${path.module}/deploy.sh"
  content  = <<-EOT
#!/bin/bash
# Simple deployment script for ${var.service_name}

# Build and push Docker image
docker build -t gcr.io/${var.project_id}/${var.service_name}:latest .
docker push gcr.io/${var.project_id}/${var.service_name}:latest

# Deploy to Cloud Run
gcloud run deploy ${var.service_name}-${var.env} \\
  --image gcr.io/${var.project_id}/${var.service_name}:latest \\
  --platform managed \\
  --region ${var.region} \\
  --allow-unauthenticated

echo "Deployed to: $(gcloud run services describe ${var.service_name}-${var.env} --platform managed --region ${var.region} --format='value(status.url)')"
EOT
  
  # Make script executable
  file_permission = "0755"
}