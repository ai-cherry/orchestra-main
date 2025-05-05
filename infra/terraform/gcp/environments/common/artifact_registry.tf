/**
 * Artifact Registry resources for orchestra project
 * Docker repository for container images
 */

# Docker repository in Artifact Registry
resource "google_artifact_registry_repository" "cherry_ai_orchestra_images" {
  project       = var.project_id
  location      = var.region
  repository_id = "orchestra-images"
  description   = "Docker repository for orchestra container images"
  format        = "DOCKER"
  
  labels = merge(local.common_labels, {
    purpose = "docker-images"
  })
  
  # Configure cleanup policies to manage image lifecycle
  cleanup_policies {
    id     = "keep-minimum-versions"
    action = "KEEP"
    condition {
      tag_state    = "TAGGED"
      tag_prefixes = ["v", "stable", "latest"]
      newer_than   = "2592000s" # 30 days
    }
  }
  
  cleanup_policies {
    id     = "delete-old-versions"
    action = "DELETE"
    condition {
      tag_state  = "ANY"
      older_than = "5184000s" # 60 days
    }
  }
  
  # Configure CMEK encryption (optional)
  kms_key_name = null # Use Google-managed key for now
  
  # Configure virtual repository settings (optional)
  mode = "STANDARD_REPOSITORY"
}

# IAM policy for the repository
resource "google_artifact_registry_repository_iam_member" "repository_admin" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.cherry_ai_orchestra_images.name
  role       = "roles/artifactregistry.admin"
  member     = "serviceAccount:${google_service_account.github_actions_deployer.email}"
}

resource "google_artifact_registry_repository_iam_member" "repository_reader" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.cherry_ai_orchestra_images.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.orchestra_runner_sa.email}"
}

# Output
output "cherry_ai_artifact_registry_repository" {
  value       = google_artifact_registry_repository.cherry_ai_orchestra_images.name
  description = "Name of the Artifact Registry Docker repository for orchestra"
}
