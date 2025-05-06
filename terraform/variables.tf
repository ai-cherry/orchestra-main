# AI Orchestra - Core Variables
# Single source of truth for common variables

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "cherry-ai-project"
}

variable "project_number" {
  description = "The GCP project number"
  type        = string
  default     = "525398941159"
}

variable "environment_configs" {
  description = "Configuration for different environments"
  type = map(object({
    region            = string
    zone              = string
    min_instances     = number
    max_instances     = number
    cpu               = string
    memory            = string
    redis_tier        = string
    redis_memory_size = number
  }))
  default = {
    dev = {
      region            = "us-west4"
      zone              = "us-west4-a"
      min_instances     = 1
      max_instances     = 5
      cpu               = "1000m"
      memory            = "2Gi"
      redis_tier        = "BASIC"
      redis_memory_size = 1
    },
    staging = {
      region            = "us-west4"
      zone              = "us-west4-a"
      min_instances     = 2
      max_instances     = 10
      cpu               = "2000m"
      memory            = "4Gi"
      redis_tier        = "STANDARD_HA"
      redis_memory_size = 2
    },
    prod = {
      region            = "us-west4"
      zone              = "us-west4-a"
      min_instances     = 3
      max_instances     = 20
      cpu               = "4000m"
      memory            = "8Gi"
      redis_tier        = "STANDARD_HA"
      redis_memory_size = 4
    }
  }
}

variable "regions" {
  description = "Map of regions for different services"
  type        = map(string)
  default = {
    default     = "us-west4"
    workstation = "us-central1"
    pubsub      = "us-west4"
  }
}

variable "vpc_network_configs" {
  description = "VPC network configurations"
  type = map(object({
    subnet_range       = string
    vpc_connector_range = string
    redis_ip_range     = string
  }))
  default = {
    dev = {
      subnet_range       = "10.0.0.0/24"
      vpc_connector_range = "10.8.0.0/28"
      redis_ip_range     = "10.0.0.0/29"
    },
    staging = {
      subnet_range       = "10.1.0.0/24"
      vpc_connector_range = "10.9.0.0/28"
      redis_ip_range     = "10.1.0.0/29"
    },
    prod = {
      subnet_range       = "10.2.0.0/24"
      vpc_connector_range = "10.10.0.0/28"
      redis_ip_range     = "10.2.0.0/29"
    }
  }
}

variable "required_apis" {
  description = "List of APIs to enable"
  type        = list(string)
  default = [
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "firestore.googleapis.com",
    "redis.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "cloudtasks.googleapis.com",
    "pubsub.googleapis.com",
    "vpcaccess.googleapis.com",
    "workstations.googleapis.com"
  ]
}

# Default secrets to create across environments
variable "default_secrets" {
  description = "List of default secrets to create"
  type        = list(string)
  default     = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "PORTKEY_API_KEY",
    "GEMINI_API_KEY"
  ]
}

# Default service account roles
variable "default_service_account_roles" {
  description = "Default IAM roles to assign to service accounts"
  type        = map(list(string))
  default     = {
    "orchestrator" = [
      "roles/secretmanager.secretAccessor",
      "roles/aiplatform.user",
      "roles/datastore.user",
      "roles/redis.editor"
    ],
    "github-actions" = [
      "roles/run.admin", 
      "roles/storage.admin", 
      "roles/secretmanager.secretAccessor"
    ]
  }
}

variable "orchestrator_service_account" {
  description = "The service account email for the orchestrator service"
  type        = string
  default     = "orchestrator-api@cherry-ai-project.iam.gserviceaccount.com"
}

variable "env" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "The primary GCP region"
  type        = string
  default     = "us-west4"
}

variable "domain_names" {
  description = "Map of domain names for services"
  type        = map(string)
  default     = {
    api = ""
    ui  = ""
  }
}

variable "api_keys" {
  description = "Map of API keys"
  type        = map(string)
  default     = {
    main = ""
  }
  sensitive   = true
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerting"
  type        = list(string)
  default     = []
}