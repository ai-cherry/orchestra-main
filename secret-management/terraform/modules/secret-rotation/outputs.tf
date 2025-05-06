/**
 * # Outputs for Secret Rotation Module
 *
 * Output values for the created Secret Rotation resources
 */

output "function_name" {
  description = "Name of the deployed Cloud Function"
  value       = google_cloudfunctions_function.rotation_function.name
}

output "function_uri" {
  description = "URI of the deployed Cloud Function"
  value       = google_cloudfunctions_function.rotation_function.https_trigger_url
}

output "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.rotation_scheduler.name
}

output "scheduler_job_schedule" {
  description = "Schedule of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.rotation_scheduler.schedule
}

output "rotation_service_account" {
  description = "Email of the service account used by the rotation function"
  value       = google_service_account.rotation_service_account.email
}

output "scheduler_service_account" {
  description = "Email of the service account used by the scheduler"
  value       = google_service_account.scheduler_service_account.email
}

output "monitored_secrets" {
  description = "List of secrets monitored for rotation"
  value       = var.secrets_to_rotate
}
