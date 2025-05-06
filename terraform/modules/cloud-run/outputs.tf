# Outputs for the Cloud Run module

output "service_name" {
  description = "The name of the Cloud Run service"
  value       = google_cloud_run_service.service.name
}

output "service_url" {
  description = "The URL of the Cloud Run service"
  value       = google_cloud_run_service.service.status[0].url
}

output "service_id" {
  description = "The ID of the Cloud Run service"
  value       = google_cloud_run_service.service.id
}

output "latest_revision_name" {
  description = "The name of the latest revision of the Cloud Run service"
  value       = google_cloud_run_service.service.status[0].latest_created_revision_name
}

output "domain_mapping_status" {
  description = "The status of the domain mapping"
  value       = var.domain_name != "" ? google_cloud_run_domain_mapping.domain_mapping[0].status : null
}

output "secret_ids" {
  description = "The IDs of the secrets created"
  value       = { for k, v in google_secret_manager_secret.secrets : k => v.id }
  sensitive   = true
}

output "scheduler_job_name" {
  description = "The name of the Cloud Scheduler job"
  value       = var.scheduler_config != null ? google_cloud_scheduler_job.scheduler_job[0].name : null
}

output "alert_policy_name" {
  description = "The name of the Cloud Monitoring alert policy"
  value       = var.enable_monitoring ? google_monitoring_alert_policy.alert_policy[0].name : null
}