terraform {
  backend "gcs" {
    bucket  = "tfstate-cherry-ai-project"
    prefix  = "orchestra/env/dev"
    credentials = "gsa-key.json"
  }
}
