# Example usage of the github-codespaces-gcp module
# This configures repositories with Codespaces that have GCP integration

module "orchestra_codespaces" {
  source = "./modules/github-codespaces-gcp"
  
  project_id    = var.project_id
  github_owner  = "cherry-ai"
  
  codespace_repositories = [
    {
      name           = "orchestra-api"
      description    = "Orchestra API with GCP Cloud Run integration"
      visibility     = "private"
      default_branch = "main"
      gcp_permissions = [
        "roles/run.admin",
        "roles/secretmanager.secretAccessor",
        "roles/storage.objectViewer"
      ]
      machine_type   = "standardLinux32gb"
      dev_container  = "${path.module}/templates/api-devcontainer.json.tftpl"
    },
    {
      name           = "orchestra-ai-agents"
      description    = "Orchestra AI Agents with Vertex AI integration"
      visibility     = "private"
      default_branch = "main"
      gcp_permissions = [
        "roles/aiplatform.user",
        "roles/secretmanager.secretAccessor",
        "roles/storage.objectAdmin"
      ]
      machine_type   = "premiumLinux"
      dev_container  = "${path.module}/templates/ai-devcontainer.json.tftpl"
    },
    {
      name           = "orchestra-infrastructure"
      description    = "Orchestra Infrastructure as Code"
      visibility     = "private"
      default_branch = "main"
      gcp_permissions = [
        "roles/compute.admin",
        "roles/iam.serviceAccountAdmin",
        "roles/resourcemanager.projectIamAdmin"
      ]
      machine_type   = "standardLinux16gb"
      dev_container  = "${path.module}/templates/infra-devcontainer.json.tftpl"
    }
  ]
}