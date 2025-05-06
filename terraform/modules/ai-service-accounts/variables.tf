# Variables for AI Service Accounts Terraform Module

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "github_actions_sa" {
  description = "The service account email for GitHub Actions"
  type        = string
}

variable "env" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}