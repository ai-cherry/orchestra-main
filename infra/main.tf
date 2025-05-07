terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "gcs" {
    bucket  = "cherry-ai-project-terraform-state"
    prefix  = "orchestra"
  }
}

provider "google" {
  project     = "cherry-ai-project"
  region      = var.region
  zone        = "${var.region}-a"
  credentials = file("/tmp/gsa-key.json")
}

provider "google-beta" {
  project     = "cherry-ai-project"
  region      = var.region
  zone        = "${var.region}-a"
  credentials = file("/tmp/gsa-key.json")
}

# ------------ Variables --------------
variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "Environment must be one of: dev, stage, prod"
  }
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-west4"  # Changed from us-west2 to us-west4 for better network latency
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "alert_notification_emails" {
  description = "List of email addresses to notify for alerts"
  type        = list(string)
  default     = ["muslilyng@gmail.com"]  # Default notification email
}

variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "memory_size_gb" {
  description = "Memory size in GB for Redis instance"
  type        = number
  default     = 1  # 1GB for dev, should be higher for prod
}

# ------------ Storage Bucket for Terraform State --------------
resource "google_storage_bucket" "terraform_state" {
  name          = "cherry-ai-project-terraform-state"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30  # days
    }
    action {
      type = "Delete"
    }
  }
}

# ------------ Networking --------------
module "networking" {
  source = "./modules/networking"

  project_id = var.project_id
  region     = var.region
  env        = var.env
}

# ------------ Redis --------------
module "redis" {
  source = "./modules/redis"

  project_id        = var.project_id
  region            = var.region
  env               = var.env
  network_id        = module.networking.vpc_id
  memory_size_gb    = var.memory_size_gb
  redis_version     = "REDIS_6_X"
}

# ------------ Secret Manager --------------
module "secrets" {
  source = "./modules/secret-manager"

  project_id        = var.project_id
  env               = var.env
  portkey_api_key_name = "portkey-api-key"
  openrouter_api_key_name = "openrouter"
  
  secret_accessors = {
    "${module.orchestrator_run.service_account}" = [
      "${module.secrets.portkey_api_key_secret}",
      "${module.secrets.openrouter_api_key_secret}",
      "${module.redis.redis_auth_secret}"
    ]
  }
}

# ------------ Cloud Run --------------
module "orchestrator_run" {
  source = "./modules/cloud-run"

  project_id         = var.project_id
  region             = var.region
  env                = var.env
  image              = "us-west2-docker.pkg.dev/${var.project_id}/orchestra/orchestrator:latest"
  min_instances      = var.env == "prod" ? 1 : 0
  max_instances      = var.env == "prod" ? 20 : 5
  cpu_always_allocated = true
  firestore_namespace = "orchestra-${var.env}"
  vector_index_name  = "orchestra-embeddings-${var.env}"
  
  depends_on = [
    module.networking,
    module.redis,
    module.secrets
  ]
}

# ------------ Firestore --------------
module "firestore" {
  source = "./modules/firestore"

  project_id = var.project_id
  region     = var.region
  env        = var.env
}

# ------------ Pub/Sub ----------------
module "pubsub" {
  source = "./modules/pubsub"

  project_id = var.project_id
  env        = var.env
}

# ------------ Vertex Vector Search ----
module "vertex" {
  source = "./modules/vertex"

  project_id      = var.project_id
  region          = var.region
  env             = var.env
  index_replicas  = var.env == "prod" ? 2 : 1
  vector_dimension = 1536  # Assuming OpenAI embedding dimension
}

# ------------ Monitoring ----------------
module "monitoring" {
  count  = var.enable_monitoring ? 1 : 0
  source = "./modules/monitoring"
  
  project_id    = var.project_id
  region        = var.region
  env           = var.env
  service_name  = "orchestrator-api-${var.env}"
  alert_notification_emails = var.alert_notification_emails
  enable_slo_alerts = var.env == "prod"
  
  depends_on = [
    module.orchestrator_run
  ]
}

# ------------ Artifact Repository ----------
resource "google_artifact_registry_repository" "orchestra" {
  provider = google-beta
  
  location      = var.region
  repository_id = "orchestra"
  description   = "Docker repository for Orchestra services"
  format        = "DOCKER"
}

# ------------ IAM Setup ----------
resource "google_project_iam_member" "vertex_agent_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "vertex_agent_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
}

# ------------ Enable APIs --------------
resource "google_project_service" "gcp_services" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "aiplatform.googleapis.com",
    "firestore.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "vpcaccess.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# ------------ Outputs --------------
output "cloud_run_url" {
  value = module.orchestrator_run.url
  description = "URL of the Cloud Run service"
}

output "firestore_database" {
  value = module.firestore.database_id
  description = "Firestore Database ID"
}

output "pubsub_topic" {
  value = module.pubsub.topic_id
  description = "Pub/Sub Topic ID"
}

output "vector_index" {
  value = module.vertex.index_id
  description = "Vertex AI Vector Search Index ID"
}

output "redis_host" {
  value = module.redis.redis_host
  description = "Redis instance hostname"
}

output "vpc_connector_name" {
  value = module.networking.vpc_connector_name
  description = "VPC connector name for Cloud Run"
}

output "dashboard_url" {
  value = var.enable_monitoring ? "https://console.cloud.google.com/monitoring/dashboards/custom/${module.monitoring[0].dashboard_name}?project=${var.project_id}" : "Monitoring disabled"
  description = "URL to the monitoring dashboard"
}
