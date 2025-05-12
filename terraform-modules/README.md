# Terraform Best Practices for AI Orchestra

This document provides guidance on Terraform best practices for the AI Orchestra project, particularly focusing on the migration to GCP Workstations.

## Standards Enforcement

The codebase includes automated tools to enforce Terraform standards:

1. **Format**: Run `terraform fmt` to standardize formatting
2. **Validate**: Run `terraform validate` to check for valid configurations
3. **Lint**: Run `tflint` to catch common errors and best practice violations

You can apply these standards using the `apply_code_standards.py` script:

```bash
python apply_code_standards.py --no-black --no-isort --no-flake8 --no-pre-commit terraform-modules gcp_migration/terraform
```

## Module Organization

Our Terraform code follows a modular organization pattern:

```
terraform-modules/
├── cloud-workstation/        # GCP Workstation configuration
├── vertex-ai-vector-search/  # Vector search capabilities
└── other-modules/            # Additional infrastructure modules
```

Each module should have consistent structure:
- `main.tf` - Main resource definitions
- `variables.tf` - Input variable declarations
- `outputs.tf` - Output value declarations
- `versions.tf` - Required provider and version constraints
- `README.md` - Module documentation

## Variable Naming Conventions

- Use snake_case for variable names
- Use descriptive names that indicate purpose
- Group related variables together in the variables.tf file
- Document each variable with a clear description

```hcl
variable "machine_type" {
  description = "The machine type to use for the workstation (e.g., n2d-standard-32)"
  type        = string
  default     = "n2d-standard-32"
}
```

## Resource Naming Conventions

- Use descriptive names that indicate purpose
- Use consistent naming patterns across resources
- Prefix resource names with module or component name

```hcl
resource "google_workstations_workstation_cluster" "ai_cluster" {
  project                = var.project_id
  region                 = var.region
  workstation_cluster_id = "${var.prefix}-${var.cluster_name}"
  # ...
}
```

## Output Documentation

Provide useful, well-documented outputs that make modules easy to use:

```hcl
output "workstation_connection_command" {
  description = "Commands to start and connect to the workstation - run these in sequence"
  value       = <<-EOT
# Start your workstation:
gcloud workstations start ${var.workstation_name} \
  --cluster=${var.cluster_name} \
  --config=${var.config_name} \
  --region=${var.region} \
  --project=${var.project_id}
EOT
}
```

## Security Best Practices

- Always encrypt sensitive data
- Use service accounts with least privilege
- Store secrets in Secret Manager (never in Terraform files)
- Enable shielded VM options for workstations
- Configure appropriate firewall rules and network isolation

## Performance Optimization

- Use appropriate machine types for workloads
- Implement auto-shutdown for workstations when idle
- Set appropriate disk sizes (neither too small nor wastefully large)
- Use preemptible instances for non-critical workloads

## Additional Resources

- [HashiCorp Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [Google Cloud Terraform Guidelines](https://cloud.google.com/docs/terraform/best-practices-for-terraform)
- [TFLint Documentation](https://github.com/terraform-linters/tflint)
