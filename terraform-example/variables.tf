variable "project_id" {
  description = "The GCP Project ID to deploy resources"
  type        = string
  default     = ""  # Set your default project ID here or leave empty to provide at runtime
}

variable "region" {
  description = "The GCP region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Name for the storage bucket (must be globally unique)"
  type        = string
  default     = "orchestra-example-bucket"  # Change this to a unique name
}