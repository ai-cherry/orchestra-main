# Default values for vertex_workbench_config.tf

# Project ID - Replace with your actual project ID
project_id = "agi-baby-cherry"

# Region for resource deployment
region = "us-central1"

# Environment (dev, stage, prod)
env = "dev"

# Vertex AI Workbench notebook instance name
notebook_name = "vertex-workbench"

# VPC network name
network_name = "default"

# Firestore database name
firestore_db_name = "orchestrator-db"

# Redis instance name
redis_name = "orchestrator-cache"
