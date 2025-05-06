/**
 * Artifact Registry configuration for Orchestra project
 */

# Docker repository for container images
resource "google_artifact_registry_repository" "cherry_ai_orchestra_images" {
  provider = google-beta
  
  location      = var.region
  project       = var.project_id
  repository_id = "cherry-ai-me-images"
  description   = "Docker repository for Orchestra container images"
  format        = "DOCKER"
  
  cleanup_policy_dry_run = false
  
  cleanup_policies {
    id     = "keep-minimum-versions"
    action = "KEEP"
    most_recent_versions {
      package_name_prefixes = ["api", "worker", "ui"]
      keep_count = 5
    }
  }
  
  cleanup_policies {
    id     = "delete-old-versions"
    action = "DELETE"
    condition {
      older_than = "5184000s" # 60 days
    }
  }
  
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
