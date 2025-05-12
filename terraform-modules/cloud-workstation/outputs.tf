# Outputs for Cloud Workstation Module

# Resource identifiers for reference or further automation
output "workstation_cluster_id" {
  description = "The ID of the created workstation cluster - use this ID in other configurations"
  value       = google_workstations_workstation_cluster.ai_cluster.workstation_cluster_id
}

output "workstation_config_id" {
  description = "The ID of the created workstation configuration - reference for workstation administration"
  value       = google_workstations_workstation_config.ai_config.workstation_config_id
}

output "workstation_id" {
  description = "The ID of the created workstation instance - use this for direct API operations"
  value       = google_workstations_workstation.ai_workstation.workstation_id
}

output "workstation_url" {
  description = "The URL to access the workstation through the web interface - copy and paste this into your browser"
  value       = "https://${var.region}.workstations.cloud.google.com/${var.project_id}/${var.region}/${var.cluster_name}/${var.config_name}/${var.workstation_name}"
}

output "workstation_ip" {
  description = "The external IP address of the workstation (if public IP is enabled) - use for firewall configurations"
  value       = var.disable_public_ip ? "Private endpoint only" : data.google_compute_instance.workstation_vm[0].network_interface[0].access_config[0].nat_ip
}

# Data source to get workstation VM details
data "google_compute_instance" "workstation_vm" {
  count     = var.disable_public_ip ? 0 : 1
  name      = "workstation-${var.cluster_name}-${var.config_name}-${var.workstation_name}"
  zone      = "${var.region}-a"  # Assuming zone a, adjust if necessary
  project   = var.project_id
  
  # We need to wait for the workstation to be created
  depends_on = [google_workstations_workstation.ai_workstation]
}

output "jupyter_connection_command" {
  description = "Command to establish an SSH tunnel to JupyterLab - use this to securely access JupyterLab in your local browser"
  value       = var.disable_public_ip ? "JupyterLab requires a direct connection to the workstation" : <<-EOT
# To connect to JupyterLab, run the following command and then open http://localhost:8888 in your browser:
gcloud compute ssh workstation-${var.cluster_name}-${var.config_name}-${var.workstation_name} \
  --project=${var.project_id} \
  --zone=${var.region}-a \
  -- -L 8888:localhost:8888
EOT
}

output "workstation_connection_command" {
  description = "Commands to start and connect to the workstation - run these in sequence"
  value       = <<-EOT
# Start your workstation:
gcloud workstations start ${var.workstation_name} \
  --cluster=${var.cluster_name} \
  --config=${var.config_name} \
  --region=${var.region} \
  --project=${var.project_id}

# After starting, access through the web UI:
${google_workstations_workstation.ai_workstation.host}
EOT
}

output "iam_bindings" {
  description = "IAM bindings created for the service account"
  value = {
    workstation_user = "roles/workstations.user",
    ai_platform_user = "roles/aiplatform.user"
  }
}

output "service_account" {
  description = "Service account with access to the workstation"
  value       = "vertex-agent@${var.project_id}.iam.gserviceaccount.com"
}

output "machine_specs" {
  description = "Machine specifications of the workstation"
  value = {
    machine_type = var.machine_type
    gpu_type     = var.gpu_type
    gpu_count    = var.gpu_count
    disk_size_gb = var.persistent_disk_size_gb
  }
}
