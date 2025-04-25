# Cost-Optimized Alternatives for GCP Resources

## 1. Redis Instance
**Current Configuration:**
```terraform
module "redis" {
  source = "./modules/redis"
  memory_size_gb = var.memory_size_gb  # Default: 1GB
  tier = "BASIC"
}
```

**Cost-Optimized Alternative:**
```terraform
module "redis" {
  source = "./modules/redis"
  memory_size_gb = var.env == "prod" ? 1 : 0.5
  tier = "BASIC"
  
  # Consider adding for non-production:
  maintenance_window {
    day = "SUNDAY"
    start_time { hours = 2, minutes = 0 }
  }
}
```

**Savings Potential:** ~50% in dev/stage environments
**Details:** Reduce memory allocation for non-production environments. Consider scheduled maintenance windows during off-hours for updates. For truly ephemeral dev environments, consider replacing Redis with a local in-memory cache.

## 2. Cloud Run Configuration
**Current Configuration:**
```terraform
module "orchestrator_run" {
  min_instances = var.env == "prod" ? 1 : 0
  max_instances = var.env == "prod" ? 20 : 5
  cpu_always_allocated = true
}
```

**Cost-Optimized Alternative:**
```terraform
module "orchestrator_run" {
  min_instances = var.env == "prod" ? 1 : 0
  max_instances = var.env == "prod" ? 10 : 2
  cpu_always_allocated = var.env == "prod"
  
  # Add auto-scaling configuration
  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = var.env == "prod" ? "10" : "2"
        "autoscaling.knative.dev/minScale" = var.env == "prod" ? "1" : "0"
        "autoscaling.knative.dev/scaleDownDelay" = "15m"
      }
    }
  }
}
```

**Savings Potential:** 30-60% for Cloud Run costs
**Details:** Reduce maximum instances, only allocate CPU continuously in production, and optimize auto-scaling parameters to reduce over-provisioning. The scale-down delay helps prevent rapid scale-up/down cycles.

## 3. Firestore Database
**Current Configuration:**
```terraform
module "firestore" {
  source = "./modules/firestore"
  # Using default configuration
}
```

**Cost-Optimized Alternative:**
```terraform
module "firestore" {
  source = "./modules/firestore"
  
  # Add collection TTL policies for dev environments
  ttl_config = var.env != "prod" ? {
    enabled = true
    field = "expireAt"
  } : null
}
```

**Savings Potential:** 15-30% on Firestore costs
**Details:** Implement TTL policies for non-production environments to automatically clean up old data. Consider adding a scheduled export/cleanup job for cost control.

## 4. Vector Search Index
**Current Configuration:**
```terraform
module "vertex" {
  index_replicas = var.env == "prod" ? 2 : 1
  vector_dimension = 1536  # Assuming OpenAI embedding dimension
}
```

**Cost-Optimized Alternative:**
```terraform
module "vertex" {
  index_replicas = var.env == "prod" ? 2 : 1
  vector_dimension = 1536
  
  # Add deployment configuration
  deployment_group = var.env
  
  # Only create in environments where needed
  count = var.env == "dev" && var.minimal_dev ? 0 : 1
  
  # Consider smaller embeddings for dev/testing
  vector_dimension = var.env == "prod" ? 1536 : 768
}
```

**Savings Potential:** 50-70% for vector search costs in dev
**Details:** Use conditional creation to avoid deploying in minimal development environments. Consider using smaller embedding dimensions for non-production use cases.

## 5. Monitoring Configuration
**Current Configuration:**
```terraform
module "monitoring" {
  count = var.enable_monitoring ? 1 : 0
  enable_slo_alerts = var.env == "prod"
}
```

**Cost-Optimized Alternative:**
```terraform
module "monitoring" {
  count = (var.env == "prod" || var.enable_monitoring) ? 1 : 0
  enable_slo_alerts = var.env == "prod"
  
  # Reduce metrics retention and sampling rate in non-prod
  metrics_scope {
    retention_period = var.env == "prod" ? "30d" : "3d"
    sampling_rate = var.env == "prod" ? 1.0 : 0.3
  }
}
```

**Savings Potential:** 10-15% on monitoring costs
**Details:** Reduce monitoring retention and sampling rate in non-production environments while ensuring production always has monitoring enabled.

## 6. Storage Class Optimization
**Current Configuration:**
```terraform
resource "google_storage_bucket" "terraform_state" {
  storage_class = "STANDARD"
}
```

**Cost-Optimized Alternative:**
```terraform
resource "google_storage_bucket" "terraform_state" {
  storage_class = "STANDARD"
  
  # Add intelligent tiering for older state files
  lifecycle_rule {
    condition {
      age = 90
      with_state = "ARCHIVED"
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}
```

**Savings Potential:** 20-40% on storage costs
**Details:** Implement storage tiering to move older state files to less expensive storage classes automatically.

## Overall Infrastructure Recommendations

1. **Environment-Based Provisioning:**
   ```terraform
   variable "minimal_dev" {
     description = "Deploy minimal resources for development"
     type        = bool
     default     = false
   }
   ```
   Create a flag to deploy only essential services for development environments.

2. **Resource Scheduling:**
   Integrate with GCP Cloud Scheduler to automatically shut down and restart non-production environments during off-hours:
   ```terraform
   resource "google_cloud_scheduler_job" "shutdown_dev" {
     count = var.env == "dev" ? 1 : 0
     name = "dev-environment-shutdown"
     schedule = "0 22 * * 1-5"  # 10 PM weekdays
     http_target {
       uri = "https://cloud-run-uri/api/manage/shutdown"
       http_method = "POST"
     }
   }
   ```

3. **Consolidated Logging:**
   Centralize and optimize logging to reduce storage and ingestion costs:
   ```terraform
   logging_exclusion {
     name = "exclude-debug-logs"
     filter = "severity<INFO AND NOT (resource.type=cloud_run_revision AND severity=ERROR)"
     description = "Exclude debug logs except for errors in Cloud Run"
   }
   ```

4. **Spot VMs for Batch Jobs:**
   For any batch processing work, consider using Spot VMs instead of regular instances to save 60-90% on compute costs.

**Potential Annual Savings:** $2,500 - $5,000 (estimate based on typical small to medium project)
