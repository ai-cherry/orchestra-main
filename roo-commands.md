# Roo Code CLI Commands for Project Orchestra

This document lists useful CLI commands for interacting with the Roo Code AI system in Project Orchestra.

## IMPORTANT NOTE

The `roo_workflow_manager.py` script is a Roo Code integration utility that is **completely separate** from the main Project Orchestra implementation. It serves as a bridge between Roo Code AI modes and the Project Orchestra infrastructure, but is not part of the core Orchestra system.

## Basic Mode Management

```bash
# Switch to a specific mode
roo-cli mode architect    # Switch to Architect mode
roo-cli mode code         # Switch to Code mode
roo-cli mode reviewer     # Switch to Reviewer mode
roo-cli mode ask          # Switch to Ask mode
roo-cli mode strategy     # Switch to Strategy mode
roo-cli mode creative     # Switch to Creative mode
roo-cli mode debug        # Switch to Debug mode
```

## AI Task Execution

```bash
# Execute a single task in a specific mode
./roo_workflow_manager.py task --mode architect --prompt "Design a multi-agent system for GCP deployment"
./roo_workflow_manager.py task --mode code --prompt "Implement a Flask API endpoint for user authentication"
./roo_workflow_manager.py task --mode reviewer --prompt "Review the following Terraform configuration for security issues"
./roo_workflow_manager.py task --mode debug --prompt "Debug why the user authentication endpoint is returning 500 errors"

# Add context from previous operations
./roo_workflow_manager.py task --mode code --prompt "Fix the issues identified in the review" --context "$(cat /tmp/review_results.txt)"
```

## VS Code Task Integration

```bash
# Run VS Code tasks via the roo workflow manager
./roo_workflow_manager.py vscode_task --task_id terraform_plan
./roo_workflow_manager.py vscode_task --task_id terraform_validate
./roo_workflow_manager.py vscode_task --task_id deploy_cloud_run
./roo_workflow_manager.py vscode_task --task_id github_gcp_init
./roo_workflow_manager.py vscode_task --task_id github_gcp_pr
./roo_workflow_manager.py vscode_task --task_id github_gcp_deploy

# Run with inputs (for tasks that require them)
./roo_workflow_manager.py vscode_task --task_id github_gcp_sync --inputs '{"codespace": "mycodespace"}'
./roo_workflow_manager.py vscode_task --task_id github_gcp_identity --inputs '{"saName": "my-service-account", "githubRepo": "myorg/myrepo"}'
./roo_workflow_manager.py vscode_task --task_id github_gcp_import --inputs '{"region": "us-central1", "serviceName": "my-service"}'
```

## Direct Terraform Operations

```bash
# Run Terraform operations via the Roo workflow manager
./roo_workflow_manager.py terraform --operation init --working_dir infra
./roo_workflow_manager.py terraform --operation plan --working_dir infra --parameters '{"out_file": "my_plan"}'
./roo_workflow_manager.py terraform --operation apply --working_dir infra --parameters '{"plan_file": "my_plan"}'
./roo_workflow_manager.py terraform --operation get_outputs --working_dir infra
./roo_workflow_manager.py terraform --operation get_outputs --working_dir infra --parameters '{"output_name": "api_url"}'

# Run specialized Terraform operations for different directories
./roo_workflow_manager.py terraform --operation init --working_dir infra/dev
./roo_workflow_manager.py terraform --operation plan --working_dir terraform-modules/cloud-workstation
```

## GCP Operations

```bash
# Run Cloud Build with different configuration files
./roo_workflow_manager.py gcp --operation cloud_build --parameters '{"config_path": "cloudbuild.yaml"}'
./roo_workflow_manager.py gcp --operation cloud_build --parameters '{"config_path": "cloudbuild_data_sync.yaml"}'
./roo_workflow_manager.py gcp --operation cloud_build --parameters '{"config_path": "cloudbuild_migration_pipeline.yaml"}'

# Deploy directly to Cloud Run
./roo_workflow_manager.py gcp --operation deploy_cloud_run --parameters '{"service_name": "api-service", "image": "gcr.io/project-id/api-image:latest", "region": "us-central1"}'

# Get current GCP project ID
./roo_workflow_manager.py gcp --operation get_project_id
```

## GitHub Integration

```bash
# Create a new branch for AI-generated changes
./roo_workflow_manager.py github --operation create_branch --parameters '{"branch_name": "feature/ai-generated-api", "base_branch": "main"}'

# Commit changes to the current branch
./roo_workflow_manager.py github --operation commit_changes --parameters '{"message": "AI-generated API implementation", "files": ["src/api.py", "tests/test_api.py"]}'

# Create a PR for the current branch
./roo_workflow_manager.py github --operation create_pr --parameters '{"title": "AI-generated API", "body": "This PR contains AI-generated code for the API service.", "base_branch": "main"}'
```

## Complete Workflow Orchestration

```bash
# Execute a full workflow using the Strategy mode to break down tasks
./roo_workflow_manager.py workflow --task "Build a todo list API and deploy it to GCP using Cloud Run"

# Execute a workflow with predefined subtasks
./roo_workflow_manager.py workflow --task "Deploy the todo API" --subtasks workflow_examples/data_sync_workflow.json

# Example subtasks JSON file (workflow_subtasks.json):
# [
#   {"type": "mode", "mode": "architect", "task": "Design the API architecture"},
#   {"type": "mode", "mode": "code", "task": "Implement the API in Python"},
#   {"type": "mode", "mode": "reviewer", "task": "Review the code for security issues"},
#   {"type": "mode", "mode": "code", "task": "Fix any issues identified in the review"},
#   {"type": "vs_code_task", "task_id": "github_gcp_init"},
#   {"type": "terraform", "operation": "plan", "working_dir": "infra"},
#   {"type": "terraform", "operation": "apply", "working_dir": "infra"},
#   {"type": "vs_code_task", "task_id": "github_gcp_deploy"},
#   {"type": "mode", "mode": "creative", "task": "Write documentation for the API"}
# ]
```

## Memory Management

```bash
# Manually read from memory
roo-cli mcp memory_bank_read --key "architecture_plan"

# Manually write to memory
roo-cli mcp memory_bank_write --key "deployment_strategy" --content "Deploy to Cloud Run with auto-scaling"

# Update an existing memory entry
roo-cli mcp memory_bank_update --key "deployment_strategy" --content "Updated: Deploy to Cloud Run with auto-scaling and Cloud SQL"
```

## Model Selection via Portkey

```bash
# Directly use the Portkey router for model selection
roo-cli mcp portkey-router route_model_request --mode code --prompt "Write a Python function to validate JWT tokens"

# Add system prompt for better context
roo-cli mcp portkey-router route_model_request --mode code --prompt "Write a function to validate JWT tokens" --systemPrompt "You are a security-focused Python developer"
```

## Practical Workflow Examples

### Example 1: Create and Deploy a New API Feature

```bash
# Create a new branch
./roo_workflow_manager.py github --operation create_branch --parameters '{"branch_name": "feature/user-analytics"}'

# Design the feature
./roo_workflow_manager.py task --mode architect --prompt "Design a user analytics tracking system for our API"

# Implement the feature
./roo_workflow_manager.py task --mode code --prompt "Implement the user analytics tracking system as designed"

# Test the implementation
./roo_workflow_manager.py task --mode debug --prompt "Write and run tests for the user analytics system"

# Create PR with the changes
./roo_workflow_manager.py github --operation commit_changes --parameters '{"message": "Add user analytics tracking"}'
./roo_workflow_manager.py github --operation create_pr --parameters '{"title": "User Analytics Feature", "body": "Adds user analytics tracking to the API"}'
```

### Example 2: Update Infrastructure

```bash
# Design infrastructure changes
./roo_workflow_manager.py task --mode architect --prompt "Design changes to add Cloud SQL to our infrastructure"

# Implement Terraform changes
./roo_workflow_manager.py task --mode code --prompt "Update the Terraform configuration to add Cloud SQL"

# Review changes for security issues
./roo_workflow_manager.py task --mode reviewer --prompt "Review the Terraform changes for security issues"

# Plan and apply changes
./roo_workflow_manager.py terraform --operation plan --working_dir infra
./roo_workflow_manager.py terraform --operation apply --working_dir infra

# Document changes
./roo_workflow_manager.py task --mode creative --prompt "Document the new Cloud SQL infrastructure"
```

### Example 3: Automated Deployment Pipeline

```bash
# Create a complete workflow that:
# 1. Designs an API
# 2. Implements it
# 3. Tests it
# 4. Deploys it
# 5. Documents it

cat > deployment_workflow.json << EOF
[
  {"type": "mode", "mode": "architect", "task": "Design a REST API for user management"},
  {"type": "mode", "mode": "code", "task": "Implement the user management API in Python with Flask"},
  {"type": "mode", "mode": "debug", "task": "Write tests for the user management API"},
  {"type": "github", "operation": "create_branch", "parameters": {"branch_name": "feature/user-management-api"}},
  {"type": "github", "operation": "commit_changes", "parameters": {"message": "Add user management API"}},
  {"type": "vs_code_task", "task_id": "github_gcp_init"},
  {"type": "terraform", "operation": "plan", "working_dir": "infra"},
  {"type": "terraform", "operation": "apply", "working_dir": "infra"},
  {"type": "gcp", "operation": "cloud_build", "parameters": {"config_path": "cloudbuild.yaml"}},
  {"type": "mode", "mode": "creative", "task": "Write documentation for the user management API"}
]
EOF

./roo_workflow_manager.py workflow --task "Create and deploy a user management API" --subtasks deployment_workflow.json
```

Remember that the `roo_workflow_manager.py` script is a Roo Code integration utility that handles the complexity of interacting with different modes, VS Code tasks, Terraform, GCP, and GitHub. It maintains context across operations through the memory bank and provides a unified interface for your AI-driven workflows, but is completely separate from the main Project Orchestra implementation.