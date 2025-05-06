variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "env" {
  description = "Environment (dev, stage, prod)"
  type        = string
}

# VPC Network
resource "google_compute_network" "orchestrator_vpc" {
  name                    = "orchestrator-vpc-${var.env}"
  auto_create_subnetworks = false
  description             = "VPC Network for Orchestra ${var.env} environment"
}

# Subnet for Cloud Run services
resource "google_compute_subnetwork" "services_subnet" {
  name          = "orchestrator-services-${var.env}"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.orchestrator_vpc.id
  
  # Enable VPC flow logs for network monitoring
  log_config {
    aggregation_interval = "INTERVAL_5_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
  
  # Enable Private Google Access for GCP services
  private_ip_google_access = true
  
  description = "Subnet for Orchestra services in ${var.env} environment"
}

# Subnet for Redis and other internal services
resource "google_compute_subnetwork" "internal_subnet" {
  name          = "orchestrator-internal-${var.env}"
  ip_cidr_range = "10.0.16.0/20"
  region        = var.region
  network       = google_compute_network.orchestrator_vpc.id
  
  # Enable Private Google Access for GCP services
  private_ip_google_access = true
  
  description = "Subnet for internal services in ${var.env} environment"
}

# Cloud Router for NAT gateway
resource "google_compute_router" "router" {
  name    = "orchestrator-router-${var.env}"
  region  = var.region
  network = google_compute_network.orchestrator_vpc.id
  
  description = "Router for Orchestra ${var.env} environment"
}

# Cloud NAT for egress traffic
resource "google_compute_router_nat" "nat" {
  name                               = "orchestrator-nat-${var.env}"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  
  subnetwork {
    name                    = google_compute_subnetwork.services_subnet.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
  
  subnetwork {
    name                    = google_compute_subnetwork.internal_subnet.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
  
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall rule to deny all ingress by default
resource "google_compute_firewall" "deny_all_ingress" {
  name    = "orchestrator-deny-all-ingress-${var.env}"
  network = google_compute_network.orchestrator_vpc.id
  
  description = "Deny all ingress traffic by default"
  
  priority = 65534  # Just before the default allow egress rule
  
  direction = "INGRESS"
  deny {
    protocol = "all"
  }
  
  source_ranges = ["0.0.0.0/0"]
}

# Firewall rule to allow internal VPC traffic
resource "google_compute_firewall" "allow_internal" {
  name    = "orchestrator-allow-internal-${var.env}"
  network = google_compute_network.orchestrator_vpc.id
  
  description = "Allow internal VPC traffic"
  
  priority = 1000
  
  direction = "INGRESS"
  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }
  
  # Allow traffic from both subnets
  source_ranges = [
    google_compute_subnetwork.services_subnet.ip_cidr_range,
    google_compute_subnetwork.internal_subnet.ip_cidr_range
  ]
}

# Firewall rule to allow HTTPS ingress to Cloud Run
resource "google_compute_firewall" "allow_https_ingress" {
  name    = "orchestrator-allow-https-ingress-${var.env}"
  network = google_compute_network.orchestrator_vpc.id
  
  description = "Allow HTTPS ingress to Cloud Run services"
  
  priority = 1000
  
  direction = "INGRESS"
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
  
  # Allow HTTPS traffic from the internet
  source_ranges = ["0.0.0.0/0"]
  
  # Target Cloud Run services
  target_tags = ["cloud-run"]
}

# Firewall rule to allow Google health checks
resource "google_compute_firewall" "allow_health_checks" {
  name    = "orchestrator-allow-health-checks-${var.env}"
  network = google_compute_network.orchestrator_vpc.id
  
  description = "Allow Google health check probes"
  
  priority = 1000
  
  direction = "INGRESS"
  allow {
    protocol = "tcp"
  }
  
  # IP ranges used by Google health checking systems
  source_ranges = [
    "35.191.0.0/16",
    "130.211.0.0/22"
  ]
}

# Serverless VPC Access connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "orchestrator-vpc-connector-${var.env}"
  region        = var.region
  network       = google_compute_network.orchestrator_vpc.id
  ip_cidr_range = "10.9.0.0/28"  # Small CIDR range for the connector, updated to avoid conflicts
  
  # Scale the connector based on environment
  min_instances = var.env == "prod" ? 2 : 1
  max_instances = var.env == "prod" ? 10 : 3
  
  depends_on = [
    google_compute_network.orchestrator_vpc
  ]
}

# Private Service Connection for Redis and other internal services
resource "google_compute_global_address" "private_ip_range" {
  name          = "orchestrator-private-ip-range-${var.env}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.orchestrator_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.orchestrator_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

# Outputs
output "vpc_id" {
  value = google_compute_network.orchestrator_vpc.id
  description = "The ID of the VPC"
}

output "services_subnet_id" {
  value = google_compute_subnetwork.services_subnet.id
  description = "The ID of the services subnet"
}

output "internal_subnet_id" {
  value = google_compute_subnetwork.internal_subnet.id
  description = "The ID of the internal subnet"
}

output "vpc_connector_id" {
  value = google_vpc_access_connector.connector.id
  description = "The ID of the VPC access connector"
}

output "services_subnet_name" {
  value = google_compute_subnetwork.services_subnet.name
  description = "The name of the services subnet"
}

output "internal_subnet_name" {
  value = google_compute_subnetwork.internal_subnet.name
  description = "The name of the internal subnet"
}

output "vpc_connector_name" {
  value = google_vpc_access_connector.connector.name
  description = "The name of the VPC access connector"
}
