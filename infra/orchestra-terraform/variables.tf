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
  description = "Environment (dev, test, prod)"
  type        = string
  default     = "dev"
}

variable "figma_pat" {
  description = "Figma Personal Access Token"
  type        = string
  sensitive   = true
  default     = ""
}
