terraform {
  backend "gcs" {
    bucket = "tfstate-cherry-ai-me-orchestra"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "cherry-ai.me"
  region  = var.region
}

provider "google-beta" {
  project = "cherry-ai.me"
  region  = var.region
}