# Naming Conventions and Common Local Variables

locals {
  # Environment-specific settings
  environment = {
    dev = {
      name_suffix = "dev"
      is_prod     = false
      log_level   = "DEBUG"
    }
    staging = {
      name_suffix = "staging"
      is_prod     = false
      log_level   = "INFO"
    }
    prod = {
      name_suffix = ""  # No suffix for production
      is_prod     = true
      log_level   = "INFO"
    }
  }
  
  # Resource naming convention
  name_prefix = "ai-orchestra"
  
  # Common labels to apply to all resources
  common_labels = {
    managed_by = "terraform"
    project    = var.project_id
    org        = var.org
  }
}