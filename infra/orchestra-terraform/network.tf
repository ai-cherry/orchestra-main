// Modern VPC Access Connector configuration with improved options
resource "google_vpc_access_connector" "orchestra_connector" {
  name          = "orchestrator-vpc-${var.env}" // Shortened name to ensure it meets length requirements
  region        = var.region
  project       = var.project_id
  network       = "default"
  ip_cidr_range = var.vpc_connector_cidr[var.env]
  
  // Set minimum and maximum throughput for scalability
  min_throughput = var.env == "prod" ? 300 : 200
  max_throughput = var.env == "prod" ? 1000 : 500
  
  // Use standard machine type for improved performance
  machine_type  = "e2-standard-4" // Updated from e2-micro for better performance
  
  // Set minimum and maximum instances for autoscaling
  min_instances = var.env == "prod" ? 2 : 2
  max_instances = var.env == "prod" ? 10 : 5 // Increased for better scaling

  // Set maintenance window for planned updates during off-hours
  maintenance_window {
    day          = "SATURDAY"
    start_time   = {
      hours   = 2
      minutes = 0
      seconds = 0
      nanos   = 0
    }
    duration = "3600s" // 1 hour maintenance window
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      ip_cidr_range, // Ignore CIDR changes to prevent conflicts with existing connector
    ]
  }
  
  depends_on = [google_project_service.required_apis]

  timeouts {
    create = "20m"
    delete = "20m"
  }
}

// Network firewall rules for secured access
resource "google_compute_firewall" "vpc_connector_health_checks" {
  name          = "vpc-connector-health-checks-${var.env}"
  network       = "default"
  project       = var.project_id
  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
  
  allow {
    protocol = "tcp"
    ports    = ["667"]  // VPC connector health check port
  }
  
  target_tags = ["vpc-connector"]
  
  depends_on = [google_project_service.required_apis]
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

// Output connector CIDR range for network planning
output "vpc_connector_cidr" {
  value       = google_vpc_access_connector.orchestra_connector.ip_cidr_range
  description = "The CIDR range used by the VPC connector"
}
