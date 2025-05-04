/**
 * Artifact Registry resources for cherry-ai-project
 * Docker repository for container images
 */

# Docker repository in Artifact Registry
resource "google_artifact_registry_repository" "cherry_ai_orchestra_images" {
  project       = "cherry-ai-project"
  location      = "us-central1"
  repository_id = "orchestra-images"
  description   = "Docker repository for orchestra container images"
  format        = "DOCKER"
  
  labels = {
    managed-by  = "terraform"
    environment = "common"
    purpose     = "docker-images"
  }
}

# Output
output "cherry_ai_artifact_registry_repository" {
  value       = google_artifact_registry_repository.cherry_ai_orchestra_images.name
  description = "Name of the Artifact Registry Docker repository for cherry-ai-project"
}
