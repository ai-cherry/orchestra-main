#!/usr/bin/env bash
#
# Weaviate Migration Deployment Script
# ====================================
# Executes the entire Weaviate-first migration workflow:
# 1. Updates Pulumi configuration
# 2. Deploys infrastructure components on DigitalOcean
# 3. Sets up Weaviate collections (Personal, PayReady, ParagonRX, Session)
# 4. Migrates data from Dragonfly to Weaviate
# 5. Validates the migration
# 6. Provides rollback options if needed
#
# This script is designed to be AI-coder friendly with clear error handling,
# progress tracking, and detailed logging.
#
# Usage:
#   ./scripts/deploy_weaviate_migration.sh [--env ENV] [--skip-infra] [--skip-migration] [--skip-validation] [--dry-run]
#
# Options:
#   --env ENV           Environment to deploy (dev or prod, default: dev)
#   --skip-infra        Skip infrastructure deployment
#   --skip-migration    Skip data migration
#   --skip-validation   Skip migration validation
#   --dry-run           Run in dry-run mode (no actual changes)
#   --help              Show this help message
#
# Author: Orchestra AI Platform

set -e  # Exit on error

# ---- CONFIGURATION ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/weaviate_migration.log"
ENV="dev"
SKIP_INFRA=false
SKIP_MIGRATION=false
SKIP_VALIDATION=false
DRY_RUN=false
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR="$PROJECT_ROOT/backups/$TIMESTAMP"

# Default Droplet IDs - update these with your actual droplet IDs
VECTOR_DROPLET_ID=""
APP_DROPLET_ID=""

# ---- PARSE ARGUMENTS ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENV="$2"
      shift 2
      ;;
    --skip-infra)
      SKIP_INFRA=true
      shift
      ;;
    --skip-migration)
      SKIP_MIGRATION=true
      shift
      ;;
    --skip-validation)
      SKIP_VALIDATION=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --vector-droplet)
      VECTOR_DROPLET_ID="$2"
      shift 2
      ;;
    --app-droplet)
      APP_DROPLET_ID="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--env ENV] [--skip-infra] [--skip-migration] [--skip-validation] [--dry-run]"
      echo ""
      echo "Options:"
      echo "  --env ENV           Environment to deploy (dev or prod, default: dev)"
      echo "  --skip-infra        Skip infrastructure deployment"
      echo "  --skip-migration    Skip data migration"
      echo "  --skip-validation   Skip migration validation"
      echo "  --dry-run           Run in dry-run mode (no actual changes)"
      echo "  --vector-droplet ID Vector droplet ID"
      echo "  --app-droplet ID    App droplet ID"
      echo "  --help              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage information."
      exit 1
      ;;
  esac
done

# ---- HELPER FUNCTIONS ----

# Initialize log file
init_log() {
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "=== Weaviate Migration Deployment Log ($(date)) ===" > "$LOG_FILE"
  echo "Environment: $ENV" >> "$LOG_FILE"
  echo "Dry run: $DRY_RUN" >> "$LOG_FILE"
  echo "Skip infrastructure: $SKIP_INFRA" >> "$LOG_FILE"
  echo "Skip migration: $SKIP_MIGRATION" >> "$LOG_FILE"
  echo "Skip validation: $SKIP_VALIDATION" >> "$LOG_FILE"
  echo "Vector droplet ID: $VECTOR_DROPLET_ID" >> "$LOG_FILE"
  echo "App droplet ID: $APP_DROPLET_ID" >> "$LOG_FILE"
  echo "===================================================" >> "$LOG_FILE"
}

# Log message to console and log file
log() {
  local level="$1"
  local message="$2"
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  
  # Define colors for different log levels
  local color=""
  case "$level" in
    "INFO")
      color="\033[0;32m"  # Green
      ;;
    "WARN")
      color="\033[0;33m"  # Yellow
      ;;
    "ERROR")
      color="\033[0;31m"  # Red
      ;;
    "STEP")
      color="\033[0;36m"  # Cyan
      level="STEP"
      ;;
    *)
      color="\033[0m"     # No color
      ;;
  esac
  
  # Reset color
  local reset="\033[0m"
  
  # Log to console with color
  echo -e "${color}[$timestamp] [$level] $message${reset}"
  
  # Log to file without color
  echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Log an info message
info() {
  log "INFO" "$1"
}

# Log a warning message
warn() {
  log "WARN" "$1"
}

# Log an error message
error() {
  log "ERROR" "$1"
}

# Log a step message (for major steps)
step() {
  log "STEP" "$1"
  echo -e "\033[0;36m========================================\033[0m"
}

# Check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if a file exists
file_exists() {
  [[ -f "$1" ]]
}

# Check if a directory exists
dir_exists() {
  [[ -d "$1" ]]
}

# Run a command with logging
run_command() {
  local cmd="$1"
  local description="$2"
  
  info "Running: $description"
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would execute: $cmd"
    return 0
  fi
  
  # Execute command and capture output
  local output
  if output=$(eval "$cmd" 2>&1); then
    info "Command succeeded: $description"
    echo "$output" >> "$LOG_FILE"
    return 0
  else
    error "Command failed: $description"
    error "Output: $output"
    echo "$output" >> "$LOG_FILE"
    return 1
  fi
}

# Create a backup directory
create_backup_dir() {
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would create backup directory: $BACKUP_DIR"
    return 0
  fi
  
  mkdir -p "$BACKUP_DIR"
  info "Created backup directory: $BACKUP_DIR"
}

# ---- INFRASTRUCTURE DEPLOYMENT FUNCTIONS ----

# Check prerequisites
check_prerequisites() {
  step "Checking prerequisites"
  
  local missing_prereqs=false
  
  # Check for required commands
  for cmd in pulumi doctl python3 pip3 jq curl; do
    if ! command_exists "$cmd"; then
      error "Missing required command: $cmd"
      missing_prereqs=true
    fi
  done
  
  # Check for required Python packages
  for pkg in weaviate-client psycopg2 sentence-transformers; do
    if ! python3 -c "import $pkg" &>/dev/null; then
      warn "Missing Python package: $pkg (will attempt to install)"
    fi
  done
  
  # Check for Pulumi stack
  if ! pulumi stack ls 2>/dev/null | grep -q "do-$ENV"; then
    error "Missing Pulumi stack: do-$ENV"
    missing_prereqs=true
  fi
  
  # Check for DigitalOcean token
  if [[ -z "$DIGITALOCEAN_TOKEN" ]]; then
    if [[ -f "$HOME/.config/doctl/config.yaml" ]]; then
      info "Found doctl config, will use it for authentication"
    else
      error "Missing DIGITALOCEAN_TOKEN environment variable and no doctl config found"
      missing_prereqs=true
    fi
  fi
  
  # Check for droplet IDs if not skipping infrastructure
  if [[ "$SKIP_INFRA" == "false" ]]; then
    if [[ -z "$VECTOR_DROPLET_ID" || -z "$APP_DROPLET_ID" ]]; then
      error "Missing droplet IDs. Please provide --vector-droplet and --app-droplet options."
      missing_prereqs=true
    else
      # Verify droplet IDs exist
      if ! doctl compute droplet get "$VECTOR_DROPLET_ID" &>/dev/null; then
        error "Vector droplet ID not found: $VECTOR_DROPLET_ID"
        missing_prereqs=true
      fi
      if ! doctl compute droplet get "$APP_DROPLET_ID" &>/dev/null; then
        error "App droplet ID not found: $APP_DROPLET_ID"
        missing_prereqs=true
      fi
    fi
  fi
  
  if [[ "$missing_prereqs" == "true" ]]; then
    error "Missing prerequisites. Please install required tools and try again."
    exit 1
  fi
  
  info "All prerequisites satisfied"
}

# Install required Python packages
install_python_packages() {
  step "Installing required Python packages"
  
  local packages=(
    "weaviate-client"
    "psycopg2-binary"
    "sentence-transformers"
    "redis"
    "tqdm"
  )
  
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would install Python packages: ${packages[*]}"
    return 0
  fi
  
  pip3 install --upgrade "${packages[@]}"
  info "Python packages installed successfully"
}

# Setup Pulumi configuration
setup_pulumi_config() {
  step "Setting up Pulumi configuration"
  
  # Create Pulumi stack if it doesn't exist
  if ! pulumi stack ls 2>/dev/null | grep -q "do-$ENV"; then
    if [[ "$DRY_RUN" == "true" ]]; then
      info "[DRY RUN] Would create Pulumi stack: do-$ENV"
    else
      run_command "cd $PROJECT_ROOT/infra && pulumi stack init do-$ENV" "Create Pulumi stack do-$ENV"
    fi
  fi
  
  # Select the Pulumi stack
  run_command "cd $PROJECT_ROOT/infra && pulumi stack select do-$ENV" "Select Pulumi stack do-$ENV"
  
  # Set Pulumi configuration values
  local config_values=(
    "env=$ENV"
    "vector_droplet_id=$VECTOR_DROPLET_ID"
    "app_droplet_id=$APP_DROPLET_ID"
    "region=sfo2"
    "weaviate_version=1.30.1"
    "enable_acorn=true"
    "enable_agents=true"
    "postgres_db_name=orchestrator"
    "postgres_user=orchestrator"
  )
  
  for config in "${config_values[@]}"; do
    local key="${config%%=*}"
    local value="${config#*=}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
      info "[DRY RUN] Would set Pulumi config: $key=$value"
    else
      run_command "cd $PROJECT_ROOT/infra && pulumi config set $key \"$value\"" "Set Pulumi config: $key"
    fi
  done
  
  # Set secret configurations (prompt if not already set)
  local secret_configs=(
    "weaviate_api_key"
    "postgres_password"
    "ssh_private_key"
  )
  
  for secret in "${secret_configs[@]}"; do
    if ! pulumi config get "$secret" &>/dev/null; then
      if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would prompt for Pulumi secret: $secret"
      else
        info "Please enter value for secret: $secret"
        run_command "cd $PROJECT_ROOT/infra && pulumi config set --secret $secret" "Set Pulumi secret: $secret"
      fi
    else
      info "Secret already set: $secret"
    fi
  done
  
  info "Pulumi configuration setup complete"
}

# Deploy infrastructure with Pulumi
deploy_infrastructure() {
  step "Deploying infrastructure with Pulumi"
  
  # Copy the new Pulumi stack file
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would copy do_weaviate_migration_stack.py to infra directory"
  else
    run_command "cp $PROJECT_ROOT/infra/do_weaviate_migration_stack.py $PROJECT_ROOT/infra/__main__.py" "Copy Weaviate migration stack to main Pulumi entry point"
  fi
  
  # Preview the changes
  run_command "cd $PROJECT_ROOT/infra && pulumi preview --stack do-$ENV" "Preview infrastructure changes"
  
  # Prompt for confirmation before applying changes
  if [[ "$DRY_RUN" == "false" ]]; then
    echo ""
    read -p "Do you want to apply these changes? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      warn "Infrastructure deployment cancelled by user"
      return 1
    fi
  fi
  
  # Apply the changes
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would deploy infrastructure with Pulumi"
  else
    run_command "cd $PROJECT_ROOT/infra && pulumi up --stack do-$ENV --yes" "Deploy infrastructure with Pulumi"
    
    # Extract outputs
    info "Extracting Pulumi outputs"
    WEAVIATE_ENDPOINT=$(cd "$PROJECT_ROOT/infra" && pulumi stack output weaviate_endpoint --stack "do-$ENV")
    POSTGRES_DSN=$(cd "$PROJECT_ROOT/infra" && pulumi stack output postgres_dsn --stack "do-$ENV")
    VECTOR_NODE_IP=$(cd "$PROJECT_ROOT/infra" && pulumi stack output vector_node_ip --stack "do-$ENV")
    APP_NODE_IP=$(cd "$PROJECT_ROOT/infra" && pulumi stack output app_node_ip --stack "do-$ENV")
    
    # Save outputs to environment file
    cat > "$PROJECT_ROOT/.env.$ENV" << EOF
WEAVIATE_ENDPOINT=$WEAVIATE_ENDPOINT
POSTGRES_DSN=$POSTGRES_DSN
VECTOR_NODE_IP=$VECTOR_NODE_IP
APP_NODE_IP=$APP_NODE_IP
EOF
    
    info "Infrastructure deployed successfully"
    info "Weaviate endpoint: $WEAVIATE_ENDPOINT"
    info "PostgreSQL DSN: $POSTGRES_DSN"
    info "Vector node IP: $VECTOR_NODE_IP"
    info "App node IP: $APP_NODE_IP"
  fi
}

# ---- DATA MIGRATION FUNCTIONS ----

# Setup Weaviate collections
setup_weaviate_collections() {
  step "Setting up Weaviate collections"
  
  # Load environment variables
  if [[ -f "$PROJECT_ROOT/.env.$ENV" ]]; then
    source "$PROJECT_ROOT/.env.$ENV"
  fi
  
  if [[ -z "$WEAVIATE_ENDPOINT" ]]; then
    error "Missing WEAVIATE_ENDPOINT. Please check .env.$ENV file or Pulumi outputs."
    return 1
  fi
  
  # Get Weaviate API key from Pulumi
  local WEAVIATE_API_KEY
  WEAVIATE_API_KEY=$(cd "$PROJECT_ROOT/infra" && pulumi config get weaviate_api_key --stack "do-$ENV" 2>/dev/null)
  
  if [[ -z "$WEAVIATE_API_KEY" ]]; then
    error "Missing WEAVIATE_API_KEY. Please check Pulumi configuration."
    return 1
  fi
  
  # Run the collection setup script
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would run setup_weaviate_collections.py"
  else
    export WEAVIATE_ENDPOINT
    export WEAVIATE_API_KEY
    
    run_command "cd $PROJECT_ROOT && python3 scripts/setup_weaviate_collections.py" "Setup Weaviate collections"
    
    # Verify collections were created
    run_command "cd $PROJECT_ROOT && python3 scripts/setup_weaviate_collections.py --verify" "Verify Weaviate collections"
  fi
  
  info "Weaviate collections setup complete"
}

# Migrate data from Dragonfly to Weaviate
migrate_data() {
  step "Migrating data from Dragonfly to Weaviate"
  
  # Load environment variables
  if [[ -f "$PROJECT_ROOT/.env.$ENV" ]]; then
    source "$PROJECT_ROOT/.env.$ENV"
  fi
  
  if [[ -z "$WEAVIATE_ENDPOINT" ]]; then
    error "Missing WEAVIATE_ENDPOINT. Please check .env.$ENV file or Pulumi outputs."
    return 1
  fi
  
  # Get Weaviate API key from Pulumi
  local WEAVIATE_API_KEY
  WEAVIATE_API_KEY=$(cd "$PROJECT_ROOT/infra" && pulumi config get weaviate_api_key --stack "do-$ENV" 2>/dev/null)
  
  if [[ -z "$WEAVIATE_API_KEY" ]]; then
    error "Missing WEAVIATE_API_KEY. Please check Pulumi configuration."
    return 1
  fi
  
  # Get Dragonfly host (from Paperspace)
  local DRAGONFLY_HOST
  read -p "Enter Dragonfly host (Paperspace IP): " DRAGONFLY_HOST
  
  if [[ -z "$DRAGONFLY_HOST" ]]; then
    error "Missing Dragonfly host. Cannot proceed with migration."
    return 1
  fi
  
  # Run the migration script
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would run migrate_dragonfly_to_weaviate.py"
    info "[DRY RUN] Dragonfly host: $DRAGONFLY_HOST"
    info "[DRY RUN] Weaviate endpoint: $WEAVIATE_ENDPOINT"
  else
    export WEAVIATE_ENDPOINT
    export WEAVIATE_API_KEY
    export DRAGONFLY_HOST
    
    # Create backup before migration
    create_backup_dir
    
    # Backup Dragonfly data
    info "Creating Dragonfly snapshot backup"
    run_command "ssh root@$DRAGONFLY_HOST 'redis-cli SAVE && cp /var/lib/redis/dump.rdb /tmp/dragonfly_backup_$TIMESTAMP.rdb'" "Create Dragonfly snapshot"
    run_command "scp root@$DRAGONFLY_HOST:/tmp/dragonfly_backup_$TIMESTAMP.rdb $BACKUP_DIR/" "Copy Dragonfly snapshot to local backup directory"
    
    # Run migration script
    run_command "cd $PROJECT_ROOT && python3 scripts/migrate_dragonfly_to_weaviate.py --dragonfly-host $DRAGONFLY_HOST --weaviate-endpoint $WEAVIATE_ENDPOINT --weaviate-api-key $WEAVIATE_API_KEY" "Migrate data from Dragonfly to Weaviate"
  fi
  
  info "Data migration complete"
}

# Validate migration
validate_migration() {
  step "Validating migration"
  
  # Load environment variables
  if [[ -f "$PROJECT_ROOT/.env.$ENV" ]]; then
    source "$PROJECT_ROOT/.env.$ENV"
  fi
  
  if [[ -z "$WEAVIATE_ENDPOINT" || -z "$POSTGRES_DSN" ]]; then
    error "Missing required environment variables. Please check .env.$ENV file or Pulumi outputs."
    return 1
  fi
  
  # Get Weaviate API key from Pulumi
  local WEAVIATE_API_KEY
  WEAVIATE_API_KEY=$(cd "$PROJECT_ROOT/infra" && pulumi config get weaviate_api_key --stack "do-$ENV" 2>/dev/null)
  
  if [[ -z "$WEAVIATE_API_KEY" ]]; then
    error "Missing WEAVIATE_API_KEY. Please check Pulumi configuration."
    return 1
  fi
  
  # Run validation script
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would run validate_weaviate_migration.py"
  else
    export WEAVIATE_ENDPOINT
    export WEAVIATE_API_KEY
    export POSTGRES_DSN
    
    run_command "cd $PROJECT_ROOT && python3 scripts/validate_weaviate_migration.py" "Validate Weaviate migration"
    
    # Check validation results
    if [[ -f "$PROJECT_ROOT/validation_results.json" ]]; then
      local validation_passed
      validation_passed=$(jq -r '.overall_validation // false' "$PROJECT_ROOT/validation_results.json" 2>/dev/null)
      
      if [[ "$validation_passed" == "true" ]]; then
        info "Validation passed successfully"
      else
        warn "Validation failed or incomplete. Please check validation_results.json for details."
      fi
    else
      warn "Validation results file not found. Validation may have failed."
    fi
  fi
}

# ---- ROLLBACK FUNCTIONS ----

# Create rollback script
create_rollback_script() {
  step "Creating rollback script"
  
  local rollback_script="$PROJECT_ROOT/rollback_migration_$TIMESTAMP.sh"
  
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would create rollback script: $rollback_script"
    return 0
  fi
  
  # Create rollback script
  cat > "$rollback_script" << 'EOF'
#!/usr/bin/env bash
#
# Weaviate Migration Rollback Script
# ==================================
# Rolls back the Weaviate migration to the previous state.
#
# Usage:
#   ./rollback_migration_TIMESTAMP.sh [--env ENV]
#
# Options:
#   --env ENV           Environment to rollback (dev or prod, default: dev)
#   --help              Show this help message

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV="dev"
BACKUP_DIR="$(dirname "$0")/backups/TIMESTAMP"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENV="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--env ENV]"
      echo ""
      echo "Options:"
      echo "  --env ENV           Environment to rollback (dev or prod, default: dev)"
      echo "  --help              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage information."
      exit 1
      ;;
  esac
done

echo "=== Starting Weaviate Migration Rollback ==="
echo "Environment: $ENV"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Check if backup directory exists
if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "ERROR: Backup directory not found: $BACKUP_DIR"
  exit 1
fi

# Restore Pulumi stack to previous state
echo "Restoring Pulumi stack..."
cd "$SCRIPT_DIR/infra"
pulumi stack select "do-$ENV"
pulumi destroy --yes

# Restore Dragonfly data if backup exists
if [[ -f "$BACKUP_DIR/dragonfly_backup_TIMESTAMP.rdb" ]]; then
  echo "Restoring Dragonfly data..."
  # Prompt for Dragonfly host
  read -p "Enter Dragonfly host (Paperspace IP): " DRAGONFLY_HOST
  
  if [[ -n "$DRAGONFLY_HOST" ]]; then
    scp "$BACKUP_DIR/dragonfly_backup_TIMESTAMP.rdb" "root@$DRAGONFLY_HOST:/tmp/"
    ssh "root@$DRAGONFLY_HOST" "systemctl stop redis && cp /tmp/dragonfly_backup_TIMESTAMP.rdb /var/lib/redis/dump.rdb && chown redis:redis /var/lib/redis/dump.rdb && systemctl start redis"
    echo "Dragonfly data restored successfully"
  else
    echo "WARNING: No Dragonfly host provided, skipping data restoration"
  fi
fi

echo "=== Rollback completed ==="
echo "The system has been rolled back to the state before migration."
EOF

  # Replace TIMESTAMP placeholder with actual timestamp
  sed -i "s/TIMESTAMP/$TIMESTAMP/g" "$rollback_script"
  
  # Make script executable
  chmod +x "$rollback_script"
  
  info "Rollback script created: $rollback_script"
  info "Run this script to rollback the migration if needed."
}

# ---- MAIN EXECUTION ----

# Main function
main() {
  # Initialize log
  init_log
  
  # Print banner
  echo -e "\033[1;36m"
  echo "====================================================="
  echo "  Weaviate Migration Deployment Script"
  echo "  Environment: $ENV"
  echo "  $(date)"
  echo "====================================================="
  echo -e "\033[0m"
  
  # Check prerequisites
  check_prerequisites
  
  # Install required Python packages
  install_python_packages
  
  # Create backup directory
  create_backup_dir
  
  # Deploy infrastructure if not skipped
  if [[ "$SKIP_INFRA" == "false" ]]; then
    setup_pulumi_config
    deploy_infrastructure
  else
    info "Skipping infrastructure deployment"
  fi
  
  # Setup Weaviate collections
  setup_weaviate_collections
  
  # Migrate data if not skipped
  if [[ "$SKIP_MIGRATION" == "false" ]]; then
    migrate_data
  else
    info "Skipping data migration"
  fi
  
  # Validate migration if not skipped
  if [[ "$SKIP_VALIDATION" == "false" ]]; then
    validate_migration
  else
    info "Skipping migration validation"
  fi
  
  # Create rollback script
  create_rollback_script
  
  # Print completion message
  echo -e "\033[1;32m"
  echo "====================================================="
  echo "  Weaviate Migration Deployment Complete"
  echo "  Log file: $LOG_FILE"
  echo "  Backup directory: $BACKUP_DIR"
  echo "  Rollback script: $PROJECT_ROOT/rollback_migration_$TIMESTAMP.sh"
  echo "====================================================="
  echo -e "\033[0m"
}

# Execute main function
main
