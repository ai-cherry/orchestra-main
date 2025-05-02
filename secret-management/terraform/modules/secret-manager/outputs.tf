/**
 * # Outputs for Secret Manager Module
 *
 * Output values for the created Secret Manager resources
 */

output "secret_ids" {
  description = "Map of secret IDs created by this module"
  value       = { for k, v in google_secret_manager_secret.secret : k => v.secret_id }
}

output "secret_names" {
  description = "Map of fully-qualified secret names"
  value       = { for k, v in google_secret_manager_secret.secret : k => v.name }
}

output "secret_versions" {
  description = "Map of secret versions created by this module"
  value       = { for k, v in google_secret_manager_secret_version.secret_version : k => v.name }
  sensitive   = true
}

output "secret_version_data" {
  description = "Map of secret data for each created version"
  value       = { for k, v in google_secret_manager_secret_version.secret_version : k => v.secret_data }
  sensitive   = true
}

output "iam_bindings" {
  description = "Map of IAM bindings applied to each secret"
  value = {
    for k, v in google_secret_manager_secret_iam_binding.secret_accessor : k => {
      role    = v.role
      members = v.members
    }
  }
}

output "access_urls" {
  description = "URLs that can be used to access the secrets via the API"
  value = {
    for k, v in google_secret_manager_secret.secret : k => 
      "https://secretmanager.googleapis.com/v1/${v.name}/versions/latest:access"
  }
}
