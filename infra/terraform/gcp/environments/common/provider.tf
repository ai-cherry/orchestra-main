# Provider configurations are defined in main.tf
# This file is kept for documentation purposes only

provider "google" {
  project = "cherry-ai.me"
  region  = var.region
}

provider "google-beta" {
  project = "cherry-ai.me"
  region  = var.region
}