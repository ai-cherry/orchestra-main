# terragrunt.hcl
# This is a basic Terragrunt configuration file that shows how to use Terragrunt
# with your Terraform code

# Include all settings from the root terragrunt.hcl file
include {
  path = find_in_parent_folders()
}

# These are the variables we want to pass to our Terraform code
terraform {
  # Source can be a local path or a remote Git repository
  source = "./"
  
  # Configure extra command line arguments to pass to Terraform for specific commands
  extra_arguments "common_vars" {
    commands = ["plan", "apply", "destroy"]
    
    arguments = [
      "-var-file=${get_terragrunt_dir()}/terraform.tfvars",
    ]
  }
}

# Set inputs to be passed to the Terraform code
inputs = {
  # You can override variables defined in variables.tf
  region = "us-central1"
  
  # Add a timestamp to make bucket name unique
  bucket_name = "orchestra-example-${get_env("USER", "default")}-${formatdate("YYMMDDhhmmss", timestamp())}"
}