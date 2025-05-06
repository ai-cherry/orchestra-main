# AI Orchestra Development Environment Terraform Configuration

terraform {
  backend "gcs" {
    bucket = "cherry-ai-project-terraform-state"
    prefix = "terraform/state/dev"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Local variables
locals {
  env = "dev"
}

# Secure credentials module
module "secure_credentials" {
  source      = "../../modules/secure-credentials"
  project_id  = var.project_id
  region      = var.region
  env         = local.env
  github_org  = var.github_org
  github_repo = var.github_repo
}

# Networking module
module "networking" {
  source     = "../../modules/networking"
  project_id = var.project_id
  region     = var.region
  env        = local.env
}

# Database module
module "database" {
  source     = "../../modules/database"
  project_id = var.project_id
  region     = var.region
  env        = local.env
  network_id = module.networking.network_id
}

# Redis module
module "redis" {
  source     = "../../modules/redis"
  project_id = var.project_id
  region     = var.region
  env        = local.env
  network_id = module.networking.network_id
}

# Cloud Run service
module "cloud_run" {
  source                   = "../../modules/cloud-run"
  project_id               = var.project_id
  region                   = var.region
  env                      = local.env
  service_name             = "ai-orchestra"
  image                    = "gcr.io/${var.project_id}/ai-orchestra:${local.env}-latest"
  service_account_email    = module.secure_credentials.service_account_emails["orchestrator"]
  redis_host_secret        = module.secure_credentials.secret_names["redis-host"]
  redis_password_secret    = module.secure_credentials.secret_names["redis-password"]
  vertex_api_key_secret    = module.secure_credentials.secret_names["vertex-api-key"]
  min_instances            = var.min_instances
  max_instances            = var.max_instances
  cpu                      = var.cpu
  memory                   = var.memory
  vpc_connector_id         = module.networking.vpc_connector_id
  allow_unauthenticated    = true
}

# Outputs
output "service_url" {
  description = "The URL of the deployed service"
  value       = module.cloud_run.service_url
}

output "service_account_emails" {
  description = "The emails of the created service accounts"
  value       = module.secure_credentials.service_account_emails
}

output "database_connection_name" {
  description = "The connection name of the database instance"
  value       = module.database.connection_name
}

output "redis_host" {
  description = "The Redis host"
  value       = module.redis.host
  sensitive   = true
}