/**
 * Terraform backend configuration for common environment
 */

terraform {
  backend "gcs" {
    bucket = "tfstate-cherry-ai-orchestra"
    prefix = "terraform/state/common"
  }
}
