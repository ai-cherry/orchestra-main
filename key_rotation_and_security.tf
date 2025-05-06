# Terraform configuration for automated service account key rotation and security enhancements
# Includes KMS setup, automatic key rotation, and VPC Service Controls

# KMS Key Ring for securely managing encryption keys
resource "google_kms_key_ring" "vertex_agent_keyring" {
  name     = "vertex-agent-keyring"
  location = "global"
  project  = var.project_id
}

# KMS Crypto Key with automatic rotation
resource "google_kms_crypto_key" "vertex_agent_key" {
  name            = "vertex-agent-key"
  key_ring        = google_kms_key_ring.vertex_agent_keyring.id
  rotation_period = "7776000s"  # 90 days rotation
  
  # Destroy in 30 days if disabled (security best practice)
  destroy_scheduled_duration = "2592000s"
  
  # Enable key for usage with service accounts
  purpose = "ENCRYPT_DECRYPT"
  
  # Version template to ensure proper algorithm
  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "SOFTWARE"
  }
}

# Give service account permission to use the KMS key
resource "google_kms_crypto_key_iam_binding" "crypto_key_binding" {
  crypto_key_id = google_kms_crypto_key.vertex_agent_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
  ]
}

# Secret Manager for securely storing and rotating service account keys
resource "google_secret_manager_secret" "vertex_agent_key_secret" {
  secret_id = "vertex-agent-key"
  project   = var.project_id
  
  replication {
    automatic = true
  }
  
  # Ensure secret gets automatic rotation
  rotation {
    next_rotation_time = timeadd(timestamp(), "2160h")  # 90 days
    rotation_period    = "7776000s"  # 90 days
  }
}

# IAM policy for service account key access
resource "google_secret_manager_secret_iam_binding" "secret_iam" {
  secret_id = google_secret_manager_secret.vertex_agent_key_secret.id
  role      = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
  ]
  project = var.project_id
}

# VPC Service Controls perimeter for enhancing security
resource "google_access_context_manager_service_perimeter" "ai_perimeter" {
  count          = var.enable_vpc_sc ? 1 : 0
  parent         = "accessPolicies/${var.access_policy_id}"
  name           = "accessPolicies/${var.access_policy_id}/servicePerimeters/ai_vertex_perimeter"
  title          = "AI Vertex Perimeter"
  perimeter_type = "PERIMETER_TYPE_REGULAR"
  
  status {
    restricted_services = [
      "aiplatform.googleapis.com",
      "compute.googleapis.com",
      "storage.googleapis.com",
      "workstations.googleapis.com"
    ]
    
    resources = [
      "projects/${var.project_id}"
    ]
    
    # Define access levels
    access_levels = [
      "accessPolicies/${var.access_policy_id}/accessLevels/trusted_workstations"
    ]
    
    # Define VPC accessible services
    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = ["RESTRICTED-SERVICES"]
    }
  }
}

# Access level for trusted locations/workstations
resource "google_access_context_manager_access_level" "trusted_workstations" {
  count       = var.enable_vpc_sc ? 1 : 0
  parent      = "accessPolicies/${var.access_policy_id}"
  name        = "accessPolicies/${var.access_policy_id}/accessLevels/trusted_workstations"
  title       = "Trusted Workstations"
  description = "Access level for trusted cloud workstations"
  
  basic {
    conditions {
      ip_subnetworks = var.trusted_ip_ranges
      
      # Require specific device policies
      device_policy {
        require_screen_lock          = true
        require_corp_owned           = true
        os_constraints {
          os_type = "DESKTOP_CHROME_OS"
        }
      }
      
      # Require specific regions
      regions = [
        "US",
        "CA"
      ]
    }
  }
}

# Alert policy for critical service account operations
resource "google_monitoring_alert_policy" "service_account_alert" {
  display_name = "Service Account Key Access Alert"
  combiner     = "OR"
  project      = var.project_id
  
  conditions {
    display_name = "Service Account Key Created"
    condition_threshold {
      filter          = "resource.type=\"service_account\" AND protoPayload.methodName=\"google.iam.admin.v1.CreateServiceAccountKey\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_COUNT"
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = var.notification_channels
  
  documentation {
    content   = "A service account key was created. This should be an audited operation."
    mime_type = "text/markdown"
  }
}

# Budget alerts to detect unexpected costs
resource "google_billing_budget" "migration_budget" {
  billing_account = var.billing_account_id
  display_name    = "Migration and Workstation Budget"
  
  budget_filter {
    projects = ["projects/${var.project_id}"]
    services = ["services/aiplatform.googleapis.com", "services/workstations.googleapis.com"]
  }
  
  amount {
    specified_amount {
      currency_code = "USD"
      units         = "1000"  # $1,000 budget
    }
  }
  
  threshold_rules {
    threshold_percent = 0.5  # Alert at 50% of budget
    spend_basis       = "CURRENT_SPEND"
  }
  
  threshold_rules {
    threshold_percent = 0.9  # Alert at 90% of budget
    spend_basis       = "CURRENT_SPEND"
  }
  
  all_updates_rule {
    monitoring_notification_channels = var.notification_channels
    pubsub_topic                     = var.budget_alert_pubsub_topic
  }
}

# Variables for configuration
variable "enable_vpc_sc" {
  description = "Whether to enable VPC Service Controls"
  type        = bool
  default     = false
}

variable "access_policy_id" {
  description = "Access Context Manager policy ID"
  type        = string
  default     = ""
}

variable "trusted_ip_ranges" {
  description = "List of trusted IP CIDR ranges for VPC SC"
  type        = list(string)
  default     = []
}

variable "notification_channels" {
  description = "List of notification channel IDs"
  type        = list(string)
  default     = []
}

variable "billing_account_id" {
  description = "Billing account ID for budget alerts"
  type        = string
  default     = ""
}

variable "budget_alert_pubsub_topic" {
  description = "PubSub topic for budget alerts"
  type        = string
  default     = ""
}
