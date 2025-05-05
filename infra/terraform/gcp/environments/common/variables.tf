variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "region" {
  description = "The GCP region where resources will be created"
  type        = string
  default     = "us-west4"
}
