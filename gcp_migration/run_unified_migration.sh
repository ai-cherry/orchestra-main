#!/bin/bash
# =============================================================================
# AI Orchestra Unified Migration Script
# =============================================================================
# This script provides a simple interface to run the unified migration executor
# with common options. It handles command line parameters and environment setup.
#
# Usage:
#   ./run_unified_migration.sh [options]
#
# Options:
#   --full              Run full migration (default)
#   --component NAME    Run specific component migration
#   --validate          Run only validation phase
#   --resume            Resume migration from last checkpoint
#   --dry-run           Perform a dry run (no actual changes)
#   --env ENV           Set environment (development/staging/production)
#   --force             Force migration even if prerequisites aren't met
#   --debug             Enable debug logging
#   --help              Display this help message
#
# Examples:
#   ./run_unified_migration.sh --full
#   ./run_unified_migration.sh --component vector-index-creation
#   ./run_unified_migration.sh --validate
#   ./run_unified_migration.sh --resume
#   ./run_unified_migration.sh --dry-run
#
# =============================================================================

set -e

# Default values
MODE="full"
COMPONENT=""
RESUME=false
DRY_RUN=false
ENV="development"
FORCE=false
DEBUG=false
CHECKPOINT_PATH="migration_state.json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --full)
      MODE="full"
      shift
      ;;
    --component)
      MODE="component"
      COMPONENT="$2"
      shift 2
      ;;
    --validate)
      MODE="validate"
      shift
      ;;
    --resume)
      RESUME=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --env)
      ENV="$2"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --checkpoint)
      CHECKPOINT_PATH="$2"
      shift 2
      ;;
    --help)
      echo "AI Orchestra Unified Migration Script"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --full              Run full migration (default)"
      echo "  --component NAME    Run specific component migration"
      echo "  --validate          Run only validation phase"
      echo "  --resume            Resume migration from last checkpoint"
      echo "  --dry-run           Perform a dry run (no actual changes)"
      echo "  --env ENV           Set environment (development/staging/production)"
      echo "  --force             Force migration even if prerequisites aren't met"
      echo "  --debug             Enable debug logging"
      echo "  --checkpoint PATH   Path to checkpoint file (default: migration_state.json)"
      echo "  --help              Display this help message"
      echo ""
      echo "Examples:"
      echo "  $0 --full"
      echo "  $0 --component vector-index-creation"
      echo "  $0 --validate"
      echo "  $0 --resume"
      echo "  $0 --dry-run"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Set up environment
export DEPLOYMENT_ENV="$ENV"

# Setup Python path to include project directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Configure logging
if [ "$DEBUG" = true ]; then
  export LOG_LEVEL="DEBUG"
else
  export LOG_LEVEL="INFO"
fi

# Ensure required Python packages
echo "Checking dependencies..."
python -c "import google.cloud.aiplatform, google.cloud.firestore, requests" 2>/dev/null || {
  echo "Missing required Python packages. Installing..."
  if [ -f "$PROJECT_DIR/pyproject.toml" ]; then
    echo "Poetry project detected, installing dependencies..."
    cd "$PROJECT_DIR" && poetry install
  else
    echo "Installing dependencies with pip..."
    pip install google-cloud-aiplatform google-cloud-firestore requests
  fi
}

# Check for gcloud CLI if force flag is not set
if [ "$FORCE" = false ]; then
  echo "Checking for gcloud CLI..."
  if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install it or use --force to continue anyway."
    exit 1
  fi
  
  # Check for authentication
  echo "Checking GCP authentication..."
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Error: Not authenticated with GCP. Please run 'gcloud auth login' or use --force to continue anyway."
    exit 1
  fi
fi

# Build command arguments
ARGS=""

if [ "$RESUME" = true ]; then
  ARGS="--resume"
else
  ARGS="--mode $MODE"
  
  if [ "$MODE" = "component" ] && [ ! -z "$COMPONENT" ]; then
    ARGS="$ARGS --component $COMPONENT"
  fi
fi

if [ "$DRY_RUN" = true ]; then
  ARGS="$ARGS --dry-run"
fi

ARGS="$ARGS --checkpoint $CHECKPOINT_PATH"

# Execute the migration
echo "Starting unified migration in $MODE mode..."
echo "Environment: $ENV"
echo "Command: python $SCRIPT_DIR/execute_unified_migration.py $ARGS"
echo "-------------------------------------------------------------"

python "$SCRIPT_DIR/execute_unified_migration.py" $ARGS

# Check result
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "Migration completed successfully!"
  
  # Show report if it exists
  if [ -f "migration_report.md" ]; then
    echo "-------------------------------------------------------------"
    echo "Migration Report Summary:"
    echo "-------------------------------------------------------------"
    grep -A 7 "^## Summary" migration_report.md
    echo "-------------------------------------------------------------"
    echo "See migration_report.md for full details"
  fi
  
  exit 0
else
  echo "Migration failed with exit code $EXIT_CODE"
  echo "Check the logs for details"
  exit $EXIT_CODE
fi