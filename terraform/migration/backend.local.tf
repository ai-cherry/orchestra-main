# Local backend configuration for development
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
