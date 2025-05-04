# Outputs for Cloud Workstation Module

output "workstation_cluster_id" {
  description = "The ID of the created workstation cluster"
  value       = google_workstations_workstation_cluster.ai_cluster.workstation_cluster_id
}

output "workstation_config_id" {
  description = "The ID of the created workstation configuration"
  value       = google_workstations_workstation_config.ai_config.workstation_config_id
}

output "workstation_id" {
  description = "The ID of the created workstation instance"
  value       = google_workstations_workstation.ai_workstation.workstation_id
}

output "workstation_url" {
  description = "The URL to access the workstation"
  value       = "https://${var.region}.workstations.cloud.google.com/${var.project_id}/${var.region}/${var.cluster_name}/${var.config_name}/${var.workstation_name}"
}

output "workstation_ip" {
  description = "The external IP address of the workstation (if public IP is enabled)"
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
  description = "Command to connect to JupyterLab running on the workstation"
  value       = var.disable_public_ip ? "JupyterLab requires a direct connection to the workstation" : "gcloud compute ssh workstation-${var.cluster_name}-${var.config_name}-${var.workstation_name} --project=${var.project_id} --zone=${var.region}-a -- -L 8888:localhost:8888"
}

output "workstation_connection_command" {
  description = "Command to start and connect to the workstation"
  value       = "gcloud workstations start ${var.workstation_name} --cluster=${var.cluster_name} --config=${var.config_name} --region=${var.region} --project=${var.project_id}"
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
