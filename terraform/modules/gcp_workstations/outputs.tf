# Output variables for the GCP Workstations module

output "workstation_cluster_id" {
  description = "ID of the workstation cluster"
  value       = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
}

output "workstation_config_id" {
  description = "ID of the workstation configuration"
  value       = google_workstations_workstation_config.orchestra_config.workstation_config_id
}

output "workstation_id" {
  description = "ID of the default workstation"
  value       = google_workstations_workstation.default_workstation.workstation_id
}

output "workstation_service_account_email" {
  description = "Email of the service account used by workstations"
  value       = google_service_account.workstation_service_account.email
}

output "workstation_bucket_name" {
  description = "Name of the GCS bucket for workstation data"
  value       = google_storage_bucket.workstation_data.name
}

output "workstation_cluster_endpoint" {
  description = "Endpoint URL for the workstation cluster"
  value       = "https://us-central1-workstations.cloud.google.com/clusters/${google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id}/configs/${google_workstations_workstation_config.orchestra_config.workstation_config_id}/workstations/${google_workstations_workstation.default_workstation.workstation_id}"
}

output "container_registry_id" {
  description = "ID of the Artifact Registry for container images"
  value       = google_artifact_registry_repository.container_registry.name
}

output "container_registry_location" {
  description = "Location of the Artifact Registry"
  value       = google_artifact_registry_repository.container_registry.location
}