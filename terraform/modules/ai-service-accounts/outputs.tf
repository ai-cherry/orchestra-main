# Outputs for AI Service Accounts Terraform Module

output "vertex_power_user_email" {
  description = "Email address of the Vertex AI Power User service account"
  value       = google_service_account.vertex_power_user.email
}

output "gemini_power_user_email" {
  description = "Email address of the Gemini Power User service account"
  value       = google_service_account.gemini_power_user.email
}

output "vertex_power_key_secret_id" {
  description = "Secret ID for the Vertex AI Power User service account key"
  value       = google_secret_manager_secret.vertex_power_key.secret_id
}

output "gemini_power_key_secret_id" {
  description = "Secret ID for the Gemini Power User service account key"
  value       = google_secret_manager_secret.gemini_power_key.secret_id
}

output "vertex_power_user_id" {
  description = "Unique ID of the Vertex AI Power User service account"
  value       = google_service_account.vertex_power_user.unique_id
}

output "gemini_power_user_id" {
  description = "Unique ID of the Gemini Power User service account"
  value       = google_service_account.gemini_power_user.unique_id
}