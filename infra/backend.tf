terraform {
  backend "gcs" {
    bucket  = "tfstate-cherry-ai-orchestra"
    prefix  = "orchestra/env/dev"
    credentials = "gsa-key.json"
  }
}
