# Terraform Backend Configuration
# Configures the GCS backend for storing Terraform state

terraform {
  backend "gcs" {
    bucket = "cherry-ai-project-terraform-state"
    prefix = "terraform/state"
  }
}