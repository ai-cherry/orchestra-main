#!/bin/bash
# Terraform Optimizer Script
# This script provides optimized Terraform operations across environments

set -e

# Configuration
SCRIPT_VERSION="1.0.0"
DEFAULT_PARALLELISM=10
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_ENVIRONMENTS=(
  "infra/terraform/gcp/environments/common"
  "infra/terraform/gcp/environments/dev"
  "infra/terraform/gcp/environments/prod"
)
LOG_DIR="${ROOT_DIR}/terraform_logs"
BACKUP_DIR="${ROOT_DIR}/terraform_backups"
LOCK_FILE="${ROOT_DIR}/.terraform_operation.lock"
DEFAULT_GCP_PROJECT="cherry-ai-project"

# Color configuration
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure directories exist
mkdir -p "${LOG_DIR}"
mkdir -p "${BACKUP_DIR}"

# Function to display help message
show_help() {
  echo -e "${BLUE}Terraform Optimizer Script v${SCRIPT_VERSION}${NC}"
  echo ""
  echo "Usage: $0 [options] <command> [environment]"
  echo ""
  echo "Commands:"
  echo "  init         Initialize terraform in specified environment(s)"
  echo "  plan         Generate and show terraform plan"
  echo "  apply        Apply terraform changes"
  echo "  destroy      Destroy terraform resources"
  echo "  validate     Validate terraform configuration"
  echo "  fmt          Format terraform files"
  echo "  backup       Backup terraform state files"
  echo "  restore      Restore terraform state from backup"
  echo "  clean        Clean terraform cache and lock files"
  echo "  show         Show current state or saved plan"
  echo ""
  echo "Environments:"
  echo "  common       Common environment"
  echo "  dev          Development environment"
  echo "  prod         Production environment"
  echo "  all          All environments (default)"
  echo ""
  echo "Options:"
  echo "  -p, --project <project-id>   Specify GCP project ID (default: ${DEFAULT_GCP_PROJECT})"
  echo "  -j, --parallelism <n>        Number of parallel operations (default: ${DEFAULT_PARALLELISM})"
  echo "  -a, --auto-approve           Skip interactive approval for apply/destroy"
  echo "  -b, --backup                 Create state backup before operation"
  echo "  -v, --verbose                Enable verbose output"
  echo "  -h, --help                   Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 init all                  Initialize all environments"
  echo "  $0 plan dev                  Create plan for dev environment"
  echo "  $0 -p my-project apply prod  Apply changes to prod with specific project ID"
  echo "  $0 -b -j 20 apply dev        Apply with backup and 20 parallel operations"
}

# Function to log messages
log() {
  local level="$1"
  local message="$2"
  local color=""
  
  case "${level}" in
    "INFO") color="${GREEN}" ;;
    "WARN") color="${YELLOW}" ;;
    "ERROR") color="${RED}" ;;
    *) color="${BLUE}" ;;
  esac
  
  echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}${NC}"
  
  # Log to file
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}" >> "${LOG_DIR}/terraform_$(date '+%Y%m%d').log"
}

# Function to backup state
backup_state() {
  local env_path="$1"
  local env_name=$(basename "${env_path}")
  
  if [[ ! -d "${env_path}/.terraform" ]]; then
    log "WARN" "No .terraform directory found in ${env_path}"
    return 0
  fi
  
  local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
  local backup_path="${BACKUP_DIR}/${env_name}_${backup_timestamp}"
  
  log "INFO" "Backing up state for ${env_name} environment"
  mkdir -p "${backup_path}"
  
  if [[ -f "${env_path}/terraform.tfstate" ]]; then
    cp "${env_path}/terraform.tfstate" "${backup_path}/terraform.tfstate"
  fi
  
  if [[ -f "${env_path}/.terraform/terraform.tfstate" ]]; then
    cp "${env_path}/.terraform/terraform.tfstate" "${backup_path}/backend.tfstate"
  fi
  
  log "INFO" "Backup completed: ${backup_path}"
}

# Function to restore state
restore_state() {
  local env_path="$1"
  local backup_name="$2"
  local env_name=$(basename "${env_path}")
  
  if [[ -z "${backup_name}" ]]; then
    # Find latest backup for environment
    backup_name=$(ls -t "${BACKUP_DIR}" | grep "^${env_name}_" | head -1)
    if [[ -z "${backup_name}" ]]; then
      log "ERROR" "No backup found for ${env_name} environment"
      return 1
    fi
  fi
  
  local backup_path="${BACKUP_DIR}/${backup_name}"
  
  if [[ ! -d "${backup_path}" ]]; then
    log "ERROR" "Backup directory not found: ${backup_path}"
    return 1
  fi
  
  log "INFO" "Restoring state for ${env_name} environment from ${backup_name}"
  
  if [[ -f "${backup_path}/terraform.tfstate" ]]; then
    cp "${backup_path}/terraform.tfstate" "${env_path}/terraform.tfstate"
  fi
  
  if [[ -f "${backup_path}/backend.tfstate" ]]; then
    mkdir -p "${env_path}/.terraform"
    cp "${backup_path}/backend.tfstate" "${env_path}/.terraform/terraform.tfstate"
  fi
  
  log "INFO" "Restore completed from: ${backup_path}"
}

# Function to run a Terraform command in an environment
run_terraform() {
  local env_path="$1"
  local command="$2"
  local args="${@:3}"
  local env_name=$(basename "${env_path}")
  
  log "INFO" "Running terraform ${command} in ${env_name} environment"
  
  # Check if environment directory exists
  if [[ ! -d "${env_path}" ]]; then
    log "ERROR" "Environment directory not found: ${env_path}"
    return 1
  fi
  
  # Create lock file
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ${USER} - ${command} - ${env_name}" > "${LOCK_FILE}"
  
  # Backup state if requested
  if [[ "${BACKUP_ENABLED}" == "true" ]]; then
    backup_state "${env_path}"
  fi
  
  # Navigate to environment directory
  pushd "${env_path}" > /dev/null
  
  # Run the command
  log "INFO" "Running: terraform ${command} ${args}"
  
  if [[ "${VERBOSE}" == "true" ]]; then
    terraform ${command} ${args}
  else
    terraform ${command} ${args} > >(tee "${LOG_DIR}/terraform_${env_name}_${command}_$(date '+%Y%m%d_%H%M%S').log") 2>&1
  fi
  
  local exit_code=$?
  
  # Return to original directory
  popd > /dev/null
  
  # Remove lock file
  rm -f "${LOCK_FILE}"
  
  if [[ "${exit_code}" -eq 0 ]]; then
    log "INFO" "Command completed successfully in ${env_name} environment"
  else
    log "ERROR" "Command failed in ${env_name} environment with exit code ${exit_code}"
    return ${exit_code}
  fi
}

# Function to run a command in specified environments
run_command() {
  local command="$1"
  local environments=("${@:2}")
  local result=0
  
  # Validate command
  case "${command}" in
    init|plan|apply|destroy|validate|fmt|show)
      # Valid terraform command
      ;;
    backup)
      # Backup all environments
      for env_path in "${environments[@]}"; do
        backup_state "${env_path}"
      done
      return 0
      ;;
    restore)
      # Restore all environments - would need a specific backup name
      log "ERROR" "Restore requires specifying a backup name"
      return 1
      ;;
    clean)
      # Clean caches in all environments
      for env_path in "${environments[@]}"; do
        local env_name=$(basename "${env_path}")
        log "INFO" "Cleaning ${env_name} environment"
        
        if [[ -d "${env_path}/.terraform" ]]; then
          find "${env_path}" -name ".terraform/providers" -type d -exec rm -rf {} + 2>/dev/null || true
          find "${env_path}" -name ".terraform.lock.hcl" -type f -delete 2>/dev/null || true
          log "INFO" "Cleaned ${env_name} environment"
        else
          log "WARN" "No .terraform directory found in ${env_path}"
        fi
      done
      return 0
      ;;
    *)
      log "ERROR" "Unknown command: ${command}"
      show_help
      return 1
      ;;
  esac
  
  # Build command arguments
  local tf_args=""
  
  if [[ "${command}" == "init" ]]; then
    tf_args="-reconfigure"
  elif [[ "${command}" == "plan" ]]; then
    tf_args="-parallelism=${PARALLELISM} -var=project_id=${PROJECT_ID} -input=false"
  elif [[ "${command}" == "apply" || "${command}" == "destroy" ]]; then
    tf_args="-parallelism=${PARALLELISM} -var=project_id=${PROJECT_ID}"
    if [[ "${AUTO_APPROVE}" == "true" ]]; then
      tf_args="${tf_args} -auto-approve"
    fi
  elif [[ "${command}" == "fmt" ]]; then
    tf_args="-recursive"
  fi
  
  # Add verbose flag if enabled
  if [[ "${VERBOSE}" == "true" && "${command}" != "fmt" ]]; then
    tf_args="${tf_args} -detailed-exitcode"
  fi
  
  # Run command in each environment
  for env_path in "${environments[@]}"; do
    run_terraform "${env_path}" "${command}" ${tf_args}
    local exit_code=$?
    
    if [[ "${exit_code}" -ne 0 ]]; then
      result=1
      
      if [[ "${command}" == "apply" || "${command}" == "destroy" ]]; then
        log "ERROR" "Operation failed in $(basename ${env_path}) environment, stopping."
        break
      fi
    fi
  done
  
  return ${result}
}

# Process options
PROJECT_ID="${DEFAULT_GCP_PROJECT}"
PARALLELISM="${DEFAULT_PARALLELISM}"
AUTO_APPROVE="false"
BACKUP_ENABLED="false"
VERBOSE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project)
      PROJECT_ID="$2"
      shift 2
      ;;
    -j|--parallelism)
      PARALLELISM="$2"
      shift 2
      ;;
    -a|--auto-approve)
      AUTO_APPROVE="true"
      shift
      ;;
    -b|--backup)
      BACKUP_ENABLED="true"
      shift
      ;;
    -v|--verbose)
      VERBOSE="true"
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    -*)
      log "ERROR" "Unknown option: $1"
      show_help
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

# Check remaining arguments
if [[ $# -lt 1 ]]; then
  log "ERROR" "No command specified"
  show_help
  exit 1
fi

COMMAND="$1"
shift

# Determine environments
if [[ $# -lt 1 || "$1" == "all" ]]; then
  ENVIRONMENTS=("${TERRAFORM_ENVIRONMENTS[@]}")
else
  case "$1" in
    common)
      ENVIRONMENTS=("${ROOT_DIR}/infra/terraform/gcp/environments/common")
      ;;
    dev)
      ENVIRONMENTS=("${ROOT_DIR}/infra/terraform/gcp/environments/dev")
      ;;
    prod)
      ENVIRONMENTS=("${ROOT_DIR}/infra/terraform/gcp/environments/prod")
      ;;
    *)
      log "ERROR" "Unknown environment: $1"
      show_help
      exit 1
      ;;
  esac
fi

# Log command execution
log "INFO" "Starting terraform operation: ${COMMAND} (Project: ${PROJECT_ID}, Parallelism: ${PARALLELISM})"

# Run the command
run_command "${COMMAND}" "${ENVIRONMENTS[@]}"
exit_code=$?

# Log operation completion
if [[ "${exit_code}" -eq 0 ]]; then
  log "INFO" "Terraform operation completed successfully"
else
  log "ERROR" "Terraform operation failed with exit code ${exit_code}"
fi

exit ${exit_code}
