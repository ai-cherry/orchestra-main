// VPC Access Connector configuration
resource "google_vpc_access_connector" "orchestra_connector" {
  name          = "orchestrator-vpc-${var.env}" // Shortened name to ensure it meets length requirements
  region        = var.region
  project       = var.project_id
  network       = "default"
  ip_cidr_range = var.vpc_connector_cidr[var.env]
  min_instances = var.env == "prod" ? 2 : 2
  max_instances = var.env == "prod" ? 5 : 3
  machine_type  = "e2-micro" // Adding explicit machine type for clarity

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      ip_cidr_range, // Ignore CIDR changes to prevent conflicts with existing connector
    ]
  }
}

// Output VPC connector name for use in deploy scripts
output "vpc_connector_name" {
  value       = google_vpc_access_connector.orchestra_connector.name
  description = "The name of the VPC connector for the current environment"
}

// Output full connector ID for use in Cloud Run deployment
output "vpc_connector_id" {
  value       = google_vpc_access_connector.orchestra_connector.id
  description = "The full ID of the VPC connector for the current environment"
}
