/**
 * Common IAM resources for the Orchestra project
 */

provider "google" {
  project = var.project_id
  region  = var.region
}
