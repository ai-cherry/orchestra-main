# GitHub SDK Integration for Terraform
# Enables GitHub repository management and GitHub Actions workflow automation

terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

# Configure the GitHub Provider
provider "github" {
  # Using GH_PAT_TOKEN environment variable for authentication
  # This is the environment variable you've saved your token as
  token = var.github_token
  
  # Owner of the GitHub repositories to manage
  owner = var.github_owner
}

# Variables for GitHub configuration
variable "github_owner" {
  description = "Owner of the GitHub repositories (organization or user)"
  type        = string
  default     = "cherry-ai"  # Default based on your organization
}

variable "github_token" {
  description = "GitHub personal access token with repo and workflow permissions"
  type        = string
  sensitive   = true
  # Default to environment variable GH_PAT_TOKEN
  default     = ""
}

# Optionally define GitHub Enterprise URL
variable "github_enterprise_url" {
  description = "URL for GitHub Enterprise (if using)"
  type        = string
  default     = ""
}

# GitHub environment variables validation module
module "github_env_validation" {
  source = "./modules/env-validation"
  count  = 0  # This is a dummy module just for documentation

  validation_rules = {
    github_token = {
      env_var_name = "GH_PAT_TOKEN"
      required     = true
      description  = "GitHub Personal Access Token with repo and workflow permissions"
    }
  }
}

# GitHub repository resource example (uncomment and modify as needed)
# resource "github_repository" "repository" {
#   name        = "example-repo"
#   description = "Example repository created and managed by Terraform"
#   visibility  = "private"
#   
#   template {
#     owner      = var.github_owner
#     repository = "terraform-template-repo"
#   }
#   
#   vulnerability_alerts = true
#   has_issues           = true
#   has_projects         = true
#   has_wiki             = true
# }

# GitHub Actions workflow settings (uncomment and modify as needed)
# resource "github_actions_secret" "repository_secret" {
#   repository      = github_repository.repository.name
#   secret_name     = "GCP_CREDENTIALS"
#   plaintext_value = var.gcp_credentials_json
# }