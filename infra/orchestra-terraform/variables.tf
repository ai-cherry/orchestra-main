variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "agi-baby-cherry"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "The environment variable must be one of 'dev', 'stage', or 'prod'."
  }
}

variable "vpc_connector_cidr" {
  description = "CIDR ranges for VPC connectors per environment"
  type        = map(string)
  default = {
    dev   = "10.8.0.0/28"
    stage = "10.8.0.16/28"
    prod  = "10.9.0.0/28" # Changed to a different subnet to avoid conflicts
  }
}

variable "figma_pat" {
  description = "Figma Personal Access Token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "create_cloud_run_services" {
  description = "Whether to create Cloud Run services"
  type        = bool
  default     = false
}

variable "phidata_agent_ui_image" {
  description = "Docker image for the Phidata Agent UI"
  type        = string
  default     = "phidata/agent_ui:1.0.0"
}
