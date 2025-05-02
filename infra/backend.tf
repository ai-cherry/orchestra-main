terraform {
  backend "gcs" {
    bucket  = "agi-baby-cherry-tfstate"
    prefix  = "orchestra/env/dev"
    credentials = "gsa-key.json"
  }
}
