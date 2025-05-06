# GitHub-GCP Integration: Repository Management with GCP Secrets
# This configuration allows managing GitHub repositories and automatically
# adding GCP service account credentials to repository secrets

# Variables for repository configuration
variable "repositories" {
  description = "Map of repositories to manage with their configurations"
  type = map(object({
    description     = string
    visibility      = string
    has_issues      = bool
    has_projects    = bool
    topics          = list(string)
    template        = optional(object({
      owner      = string
      repository = string
    }))
    google_services = list(string) # GCP services this repo needs access to
  }))
  default = {
    "orchestra-api" = {
      description     = "Orchestra API service with Terraform configuration"
      visibility      = "private"
      has_issues      = true
      has_projects    = true
      topics          = ["api", "terraform", "gcp", "cloud-run"]
      google_services = ["cloudrun.googleapis.com", "secretmanager.googleapis.com"]
    },
    "orchestra-agents" = {
      description     = "Agent service with Vertex AI integration"
      visibility      = "private"
      has_issues      = true
      has_projects    = true
      topics          = ["ai", "gcp", "vertex-ai"]
      google_services = ["aiplatform.googleapis.com"]
    }
  }
}

# GitHub repositories with GCP integration
resource "github_repository" "managed_repos" {
  for_each = var.repositories

  name        = each.key
  description = each.value.description
  visibility  = each.value.visibility
  
  has_issues    = each.value.has_issues
  has_projects  = each.value.has_projects
  has_wiki      = true
  has_downloads = true
  
  topics = each.value.topics
  
  vulnerability_alerts = true
  
  dynamic "template" {
    for_each = each.value.template != null ? [each.value.template] : []
    content {
      owner      = template.value.owner
      repository = template.value.repository
    }
  }
  
  # Auto-initialize with starter files
  auto_init = true
  
  # Add license
  license_template = "apache-2.0"
}

# Create a service account per repository
resource "google_service_account" "repo_service_accounts" {
  for_each = var.repositories
  
  account_id   = "github-${each.key}"
  display_name = "GitHub SA for ${each.key}"
  description  = "Service account for GitHub Actions in ${each.key} repository"
}

# Grant service accounts access to required GCP services
resource "google_project_iam_member" "repo_service_account_roles" {
  for_each = {
    for pair in flatten([
      for repo_name, repo in var.repositories : [
        for service in repo.google_services : {
          repo_name = repo_name
          service   = service
        }
      ]
    ]) : "${pair.repo_name}-${pair.service}" => pair
  }
  
  project = var.project_id
  role    = "roles/viewer"  # Start with minimal permissions
  member  = "serviceAccount:${google_service_account.repo_service_accounts[each.value.repo_name].email}"
}

# Create Workload Identity Federation pool for GitHub
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
}

# Create GitHub provider
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"
  
  attribute_mapping = {
    "google.subject"           = "assertion.sub"
    "attribute.repository"     = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
    "attribute.actor"          = "assertion.actor"
    "attribute.workflow"       = "assertion.workflow"
  }
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow specific GitHub repositories to use the service accounts
resource "google_service_account_iam_binding" "workload_identity_binding" {
  for_each = var.repositories
  
  service_account_id = google_service_account.repo_service_accounts[each.key].name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_owner}/${each.key}"
  ]
}

# Create GitHub Actions secrets for each repository
resource "github_actions_secret" "workload_identity_provider" {
  for_each = var.repositories
  
  repository      = github_repository.managed_repos[each.key].name
  secret_name     = "WORKLOAD_IDENTITY_PROVIDER"
  plaintext_value = google_iam_workload_identity_pool_provider.github_provider.name
}

resource "github_actions_secret" "service_account" {
  for_each = var.repositories
  
  repository      = github_repository.managed_repos[each.key].name
  secret_name     = "SERVICE_ACCOUNT"
  plaintext_value = google_service_account.repo_service_accounts[each.key].email
}