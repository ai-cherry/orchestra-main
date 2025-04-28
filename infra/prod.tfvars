# prod.tfvars - Production Environment Configuration for Orchestra

# Environment
env = "prod"
project_id = "agi-baby-cherry"  # Replace with actual production project ID if different

# Region (consider multi-region for production)
region = "us-central1"
availability_zones = ["us-central1-a", "us-central1-b", "us-central1-c"]

# Service account
service_account_id = "orchestra-prod-sa"
service_account_display_name = "Orchestra Production Service Account"

# Cloud Run configuration
cloud_run_min_instances = 2
cloud_run_max_instances = 20
cloud_run_cpu = "2"
cloud_run_memory = "4Gi"
cloud_run_timeout = 900 # 15 minutes
cloud_run_concurrency = 80

# CloudSQL configuration 
cloudsql_machine_type = "db-custom-4-8192"
cloudsql_disk_size = 50  # GB
cloudsql_availability_type = "REGIONAL"  # Use REGIONAL for production
cloudsql_maintenance_window_day = 7  # Sunday
cloudsql_maintenance_window_hour = 2  # 2AM
cloudsql_backup_enabled = true
cloudsql_backup_start_time = "00:00"  # Midnight UTC
cloudsql_backup_retention = 7  # 7 days

# Redis configuration
redis_tier = "standard"
redis_memory_size_gb = 5
redis_auth_enabled = true
redis_transit_encryption_mode = "SERVER_AUTHENTICATION"

# VPC Network
vpc_connector_name = "orchestra-prod-vpc"
use_private_endpoints = true
ip_range_services = "10.0.32.0/20"

# Security
enable_cloud_armor = true
enable_vpc_flow_logs = true

# Monitoring
enable_alerting = true
error_rate_threshold = 0.05  # 5% error rate threshold
latency_threshold_ms = 2000  # 2 seconds
