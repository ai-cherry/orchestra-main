# Terraform module for auto-provisioning GitHub Codespaces with GCP credentials
# This module creates:
# 1. GitHub repositories with Codespaces configuration
# 2. GCP service accounts for each repository
# 3. Integration between Codespaces and GCP services

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "codespace_repositories" {
  description = "List of repositories to set up with Codespaces configuration"
  type = list(object({
    name             = string
    description      = string
    visibility       = string
    default_branch   = string
    gcp_permissions  = list(string)
    machine_type     = string
    dev_container    = string
  }))
}

variable "github_owner" {
  description = "GitHub organization or user that owns the repositories"
  type        = string
}

variable "github_token_secret" {
  description = "Name of the Secret Manager secret containing the GitHub token"
  type        = string
  default     = "github-pat-token"
}

# Create GCP service accounts for Codespaces
resource "google_service_account" "codespace_accounts" {
  for_each     = { for repo in var.codespace_repositories : repo.name => repo }
  
  account_id   = "github-codespace-${each.key}"
  display_name = "GitHub Codespace for ${each.key}"
  description  = "Service account for GitHub Codespaces in ${each.key} repository"
}

# Grant necessary permissions to the service accounts
resource "google_project_iam_member" "codespace_permissions" {
  for_each = {
    for pair in flatten([
      for repo in var.codespace_repositories : [
        for permission in repo.gcp_permissions : {
          repo_name   = repo.name
          permission  = permission
        }
      ]
    ]) : "${pair.repo_name}-${pair.permission}" => pair
  }
  
  project = var.project_id
  role    = each.value.permission
  member  = "serviceAccount:${google_service_account.codespace_accounts[each.value.repo_name].email}"
}

# Create service account keys
resource "google_service_account_key" "codespace_keys" {
  for_each           = { for repo in var.codespace_repositories : repo.name => repo }
  
  service_account_id = google_service_account.codespace_accounts[each.key].name
}

# Store keys in Secret Manager
resource "google_secret_manager_secret" "codespace_sa_keys" {
  for_each  = { for repo in var.codespace_repositories : repo.name => repo }
  
  secret_id = "github-codespace-${each.key}-key"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "codespace_sa_key_versions" {
  for_each = { for repo in var.codespace_repositories : repo.name => repo }
  
  secret      = google_secret_manager_secret.codespace_sa_keys[each.key].id
  secret_data = base64decode(google_service_account_key.codespace_keys[each.key].private_key)
}

# Create GitHub repositories with Codespaces configuration
resource "github_repository" "codespace_repos" {
  for_each    = { for repo in var.codespace_repositories : repo.name => repo }
  
  name        = each.key
  description = each.value.description
  visibility  = each.value.visibility
  
  has_issues    = true
  has_wiki      = true
  has_projects  = true
  has_downloads = true
  
  vulnerability_alerts = true
  
  # Default branch configuration
  default_branch = each.value.default_branch
  
  # Auto-initialize with starter files
  auto_init = true
}

# Set up repository secrets for GCP authentication
resource "github_actions_secret" "codespace_gcp_keys" {
  for_each        = { for repo in var.codespace_repositories : repo.name => repo }
  
  repository      = github_repository.codespace_repos[each.key].name
  secret_name     = "GCP_SA_KEY"
  plaintext_value = base64decode(google_service_account_key.codespace_keys[each.key].private_key)
}

# Create .devcontainer configuration files in repositories
resource "github_repository_file" "devcontainer_json" {
  for_each   = { for repo in var.codespace_repositories : repo.name => repo }
  
  repository = github_repository.codespace_repos[each.key].name
  file       = ".devcontainer/devcontainer.json"
  content    = templatefile(each.value.dev_container, {
    project_id = var.project_id
    repo_name  = each.key
    machine_type = each.value.machine_type
  })
  branch     = github_repository.codespace_repos[each.key].default_branch
}

# Create welcome script to set up Codespace with GCP authentication
resource "github_repository_file" "welcome_script" {
  for_each   = { for repo in var.codespace_repositories : repo.name => repo }
  
  repository = github_repository.codespace_repos[each.key].name
  file       = ".devcontainer/setup-gcp.sh"
  content    = <<-EOT
#!/bin/bash
# Set up GCP authentication in Codespace
set -e

echo "🔧 Setting up Google Cloud SDK authentication..."

# Create GCP credentials directory
mkdir -p /home/vscode/.config/gcloud

# Check for GCP service account key
if [ -n "$GCP_SA_KEY" ]; then
  echo "Using provided GCP_SA_KEY environment variable..."
  echo "$GCP_SA_KEY" > /tmp/gcp-key.json
  chmod 600 /tmp/gcp-key.json
  
  # Activate service account
  gcloud auth activate-service-account --key-file=/tmp/gcp-key.json
  
  # Set default project
  gcloud config set project ${var.project_id}
  
  echo "✅ GCP authentication configured successfully!"
else
  echo "⚠️ GCP_SA_KEY not found. Please set up authentication manually:"
  echo "    gcloud auth login"
fi

echo "🚀 Welcome to your ${each.key} development environment!"
echo "    Project: ${var.project_id}"
echo "    Repository: ${each.key}"
echo "    Authenticated as: $(gcloud config get-value account)"
EOT
  branch     = github_repository.codespace_repos[each.key].default_branch
}

# Create setup script for GitHub Codespaces
resource "github_repository_file" "codespace_setup" {
  for_each   = { for repo in var.codespace_repositories : repo.name => repo }
  
  repository = github_repository.codespace_repos[each.key].name
  file       = ".github/codespace-setup.sh"
  content    = <<-EOT
#!/bin/bash
# This script runs during Codespace creation to configure GCP settings

# Install required tools
echo "📦 Installing additional tools..."
pip install --user google-cloud-storage google-cloud-pubsub google-cloud-secret-manager

# Set up Terraform
if command -v terraform &> /dev/null; then
  echo "✅ Terraform is already installed"
else
  echo "🔧 Installing Terraform..."
  wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list
  apt update && apt install -y terraform
fi

# Set up gcloud command completion
echo "source /usr/share/google-cloud-sdk/completion.bash.inc" >> ~/.bashrc

# Create helpful aliases
cat >> ~/.bashrc << EOF
# GCP helpers
alias gcp-project='gcloud config get-value project'
alias tf-plan='terraform plan'
alias tf-apply='terraform apply -auto-approve'
alias gsecrets='gcloud secrets list'
alias deploy-run='gcloud run deploy'
EOF

# Configure git
git config --global credential.helper store

echo "✅ Codespace setup complete!"
EOT
  branch     = github_repository.codespace_repos[each.key].default_branch
}

# Output the new repository URLs
output "repository_urls" {
  value = { for name, repo in github_repository.codespace_repos : name => repo.html_url }
}

# Output the GCP service account emails
output "service_account_emails" {
  value = { for name, sa in google_service_account.codespace_accounts : name => sa.email }
}

# Output codespace creation URLs
output "codespace_creation_urls" {
  value = { for name, repo in github_repository.codespace_repos : name => "https://github.com/codespaces/new?hide_repo_select=true&ref=${repo.default_branch}&repo=${var.github_owner}%2F${name}" }
}