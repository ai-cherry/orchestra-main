# Provider Configurations with Aliases

provider "google" {
  alias   = "default"
  project = var.project_id
  region  = var.regions.default
}

provider "google" {
  alias   = "us-central1"
  project = var.project_id
  region  = var.region
}

provider "google" {
  alias   = "us-west4"
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  alias   = "default"
  project = var.project_id
  region  = var.regions.default
}

provider "google-beta" {
  alias   = "us-central1"
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  alias   = "us-west4"
  project = var.project_id
  region  = var.region
}

# Default providers (for backward compatibility during migration)
provider "google" {
  project = var.project_id
  region  = var.regions.default
}

provider "google-beta" {
  project = var.project_id
  region  = var.regions.default
}