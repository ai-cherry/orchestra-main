/**
 * # GCP Secret Manager Module
 * 
 * This module provisions Google Cloud Secret Manager resources with enhanced security
 * features including zero-trust access controls and organizational tagging.
 */

# Secret resource with configurable replication
resource "google_secret_manager_secret" "secret" {
  for_each  = var.secrets
  
  secret_id = each.key
  project   = var.project_id
  
  labels    = merge(var.labels, each.value.labels)
  
  # Custom replication strategy
  replication {
    dynamic "user_managed" {
      for_each = var.replication_automatic ? [] : [1]
      content {
        dynamic "replicas" {
          for_each = var.replication_locations
          content {
            location = replicas.value
            customer_managed_encryption {
              kms_key_name = var.customer_managed_encryption_key != "" ? var.customer_managed_encryption_key : null
            }
          }
        }
      }
    }
    
    dynamic "automatic" {
      for_each = var.replication_automatic ? [1] : []
      content {}
    }
  }
  
  # Configurable rotation period
  dynamic "rotation" {
    for_each = each.value.rotation_period != null ? [1] : []
    content {
      next_rotation_time = timeadd(timestamp(), each.value.rotation_period)
      rotation_period    = each.value.rotation_period
    }
  }
  
  # Configurable expiration
  dynamic "expire_time" {
    for_each = each.value.expiration != null ? [1] : []
    content {
      expire_time = timeadd(timestamp(), each.value.expiration)
    }
  }
}

# Initial secret versions
resource "google_secret_manager_secret_version" "secret_version" {
  for_each = {
    for key, secret in var.secrets : key => secret
    if secret.initial_value != null
  }
  
  secret      = google_secret_manager_secret.secret[each.key].id
  secret_data = each.value.initial_value
}

# IAM bindings with conditional access
resource "google_secret_manager_secret_iam_binding" "secret_accessor" {
  for_each = {
    for binding in local.iam_bindings : "${binding.secret_id}-${binding.role}" => binding
  }
  
  project   = var.project_id
  secret_id = google_secret_manager_secret.secret[each.value.secret_id].secret_id
  role      = each.value.role
  members   = each.value.members
  
  dynamic "condition" {
    for_each = each.value.condition != null ? [each.value.condition] : []
    content {
      title       = condition.value.title
      description = condition.value.description
      expression  = condition.value.expression
    }
  }
}

# Generate all IAM bindings from the access map
locals {
  iam_bindings = flatten([
    for secret_id, secret in var.secrets : [
      for role, access in secret.access : {
        secret_id = secret_id
        role      = role
        members   = access.members
        condition = access.condition
      }
    ]
  ])
}
