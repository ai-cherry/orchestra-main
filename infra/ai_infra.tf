# Gemini-generated Terraform config
module "vertex_ai" {
  source  = "terraform-google-modules/vertex-ai/google"
  version = "~> 5.0"

  project_id          = "cherry-ai-project"
  region              = "us-west4"
  accelerator_config = {
    type  = "NVIDIA_TESLA_T4"
    count = 1
  }
}

resource "google_ai_platform_dataset" "code_context" {
  project       = "cherry-ai-project"
  display_name  = "code-context-dataset"
  metadata_schema_uri = "gs://google-cloud-aiplatform/schema/dataset/metadata/code_1.0.0.yaml"
}
