#!/bin/bash
# cleanup_repo.sh
#
# This script helps clean up large files from the repository history
# and performs other repository optimization tasks.
# It's part of Phase 1 of the GitHub repository size management implementation.
#
# WARNING: This script modifies git history. Make sure all team members are aware
# before running it in a shared repository.
#
# Requirements:
# - git-filter-repo: pip install git-filter-repo
# - All changes must be committed or stashed before running
#
# Usage: ./scripts/cleanup_repo.sh [options]
# Options:
#   --dry-run         Only show what would be removed without making changes
#   --branch NAME     Target specific branch (default: current default branch)
#   --all-branches    Process all branches (not just the default branch)
#   --no-backup       Skip creating a backup (NOT RECOMMENDED)
#   --quiet           Reduce output verbosity
#   --ci              Run in CI mode (non-interactive)

set -eo pipefail

# Default settings
DRY_RUN=false
SPECIFIC_BRANCH=""
ALL_BRANCHES=false
SKIP_BACKUP=false
QUIET=false
CI_MODE=false
TEMP_FILES=()
LOG_FILE="repo_cleanup_$(date +%Y%m%d%H%M%S).log"
START_TIME=$(date +%s)

# Function to log messages
log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Always write to log file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Only print to console if not in quiet mode, or if it's an error
    if [[ "$QUIET" == "false" || "$level" == "ERROR" ]]; then
        case "$level" in
            "INFO")  echo "ℹ️ $message" ;;
            "WARN")  echo "⚠️ $message" ;;
            "ERROR") echo "❌ $message" ;;
            "SUCCESS") echo "✅ $message" ;;
            *) echo "$message" ;;
        esac
    fi
}

# Function to clean up temporary files
cleanup() {
    log "INFO" "Cleaning up temporary files..."
    for temp_file in "${TEMP_FILES[@]}"; do
        if [[ -f "$temp_file" ]]; then
            rm -f "$temp_file"
        fi
    done
}

# Handle errors and cleanup on exit
handle_error() {
    local exit_code=$?
    log "ERROR" "Command failed with exit code $exit_code"
    cleanup
    exit $exit_code
}

# Set up cleanup on script exit
trap cleanup EXIT
trap handle_error ERR

# Detect default branch
detect_default_branch() {
    # Try to get default branch from git
    local default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
    
    # If not found, try to guess from common branch names
    if [[ -z "$default_branch" ]]; then
        for branch in main master development dev; do
            if git show-ref --verify --quiet refs/heads/$branch; then
                default_branch=$branch
                break
            fi
        done
    fi
    
    # If still not found, use current branch
    if [[ -z "$default_branch" ]]; then
        default_branch=$(git rev-parse --abbrev-ref HEAD)
        log "WARN" "Could not detect default branch. Using current branch: $default_branch"
    else
        log "INFO" "Detected default branch: $default_branch"
    fi
    
    echo "$default_branch"
}

# Print help
show_help() {
    echo "Usage: ./scripts/cleanup_repo.sh [options]"
    echo "Options:"
    echo "  --dry-run         Only show what would be removed without making changes"
    echo "  --branch NAME     Target specific branch (default: current default branch)"
    echo "  --all-branches    Process all branches (not just the default branch)"
    echo "  --no-backup       Skip creating a backup (NOT RECOMMENDED)"
    echo "  --quiet           Reduce output verbosity"
    echo "  --ci              Run in CI mode (non-interactive)"
    echo "  --help            Show this help message"
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --branch)
            SPECIFIC_BRANCH="$2"
            shift 2
            ;;
        --all-branches)
            ALL_BRANCHES=true
            shift
            ;;
        --no-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        --ci)
            CI_MODE=true
            QUIET=true # CI mode implies quiet
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            show_help
            ;;
    esac
done

# Log settings
log "INFO" "Starting repository cleanup with settings:"
log "INFO" "  Dry run: $DRY_RUN"
log "INFO" "  Branch: ${SPECIFIC_BRANCH:-"(default)"}"
log "INFO" "  All branches: $ALL_BRANCHES"
log "INFO" "  Skip backup: $SKIP_BACKUP"
log "INFO" "  CI mode: $CI_MODE"

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    log "ERROR" "git-filter-repo is not installed. Please install it with:"
    log "ERROR" "pip install git-filter-repo"
    exit 1
fi

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    log "ERROR" "There are uncommitted changes in the repository."
    log "ERROR" "Please commit or stash your changes before running this script."
    exit 1
fi

# Record initial repository size
INITIAL_SIZE=$(du -sh .git | awk '{print $1}')
log "INFO" "Current repository size: $INITIAL_SIZE"

# Determine branch to use
TARGET_BRANCH=""
if [[ -n "$SPECIFIC_BRANCH" ]]; then
    # Verify the branch exists
    if ! git show-ref --verify --quiet refs/heads/$SPECIFIC_BRANCH; then
        log "ERROR" "Branch '$SPECIFIC_BRANCH' does not exist"
        exit 1
    fi
    TARGET_BRANCH="$SPECIFIC_BRANCH"
else
    TARGET_BRANCH=$(detect_default_branch)
fi

# Create a backup
if [[ "$SKIP_BACKUP" == "false" ]]; then
    TIMESTAMP=$(date +%Y%m%d%H%M%S)
    BACKUP_DIR="../ai-orchestra-backup-$TIMESTAMP"
    log "INFO" "Creating backup in $BACKUP_DIR"
    if [[ "$DRY_RUN" == "false" ]]; then
        log "INFO" "Cloning repository for backup (this may take a while)..."
        git clone --mirror . "$BACKUP_DIR"
        log "SUCCESS" "Backup created at $BACKUP_DIR"
        log "INFO" "If something goes wrong, you can restore with:"
        log "INFO" "rm -rf .git && cp -r $BACKUP_DIR/.git . && git reset --hard"
    else
        log "INFO" "(Dry run: backup would be created at $BACKUP_DIR)"
    fi
else
    log "WARN" "Skipping backup creation as requested. This is not recommended!"
    if [[ "$CI_MODE" == "false" && "$DRY_RUN" == "false" ]]; then
        read -p "Are you sure you want to proceed without a backup? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "INFO" "Operation cancelled."
            exit 0
        fi
    fi
fi

log "INFO" "Analyzing repository for large files..."
# Use a secure temporary file
LARGE_FILES_LIST=$(mktemp)
TEMP_FILES+=("$LARGE_FILES_LIST")

# Find the largest files in git history
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | grep '^blob' | sort -k3nr | head -n 50 > "$LARGE_FILES_LIST"

log "INFO" "Top 50 largest files in repository history:"
cat "$LARGE_FILES_LIST" | awk '{printf "%.2f MB %s\n", $3/1024/1024, $4}' | column -t

# Files to remove (adjust these patterns based on your needs)
PATTERNS_TO_REMOVE=(
    "google-cloud-sdk"
    "*.pyc"
    "*.pyo"
    "*.so"
    "*.egg"
    "*.tar.gz"
    "*.zip"
    "*.jar"
    "*.class"
    "*.min.js"
    ".pytest_cache/"
    ".mypy_cache/"
    ".ruff_cache/"
    "__pycache__/"
    "node_modules/"
    "dist/"
    "build/"
)

log "INFO" "The following file patterns will be removed from git history:"
for pattern in "${PATTERNS_TO_REMOVE[@]}"; do
    log "INFO" "  - $pattern"
done

if [[ "$DRY_RUN" == "true" ]]; then
    log "INFO" "Dry run completed. To perform the actual cleanup, run without --dry-run"
    exit 0
fi

# Confirm before proceeding
if [[ "$CI_MODE" == "false" ]]; then
    log "WARN" "WARNING: This will permanently modify git history!"
    if [[ "$ALL_BRANCHES" == "true" ]]; then
        log "WARN" "This will affect ALL branches in the repository."
    else
        log "INFO" "This will affect branch: $TARGET_BRANCH"
    fi
    log "WARN" "All collaborators will need to clone a fresh copy after this operation."
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Operation cancelled."
        exit 0
    fi
fi

# Create a temporary file with paths to remove
PATTERNS_FILE=$(mktemp)
TEMP_FILES+=("$PATTERNS_FILE")
for pattern in "${PATTERNS_TO_REMOVE[@]}"; do
    echo "$pattern" >> "$PATTERNS_FILE"
done

# Prepare filter-repo arguments
FILTER_ARGS="--force --paths-from-file $PATTERNS_FILE --invert-paths"

# Add branch filtering if needed
if [[ "$ALL_BRANCHES" == "false" && -n "$TARGET_BRANCH" ]]; then
    FILTER_ARGS="$FILTER_ARGS --refs refs/heads/$TARGET_BRANCH"
    log "INFO" "Filtering only branch: $TARGET_BRANCH"
else
    log "INFO" "Filtering all branches"
fi

log "INFO" "Cleaning up repository history (this may take a while)..."
log "INFO" "Running: git filter-repo $FILTER_ARGS"

if [[ "$DRY_RUN" == "false" ]]; then
    # Create a progress indicator
    progress_indicator() {
        local pid=$1
        local spin='-\|/'
        local i=0
        while kill -0 $pid 2>/dev/null; do
            i=$(( (i+1) % 4 ))
            printf "\r[%c] Working... " "${spin:$i:1}"
            sleep .3
        done
        printf "\rDone!                  \n"
    }
    
    # Run git filter-repo
    git filter-repo $FILTER_ARGS &
    filter_pid=$!
    
    if [[ "$QUIET" == "false" ]]; then
        progress_indicator $filter_pid
    else
        wait $filter_pid
    fi
    
    log "INFO" "Running garbage collection..."
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    
    # Calculate size after cleanup
    FINAL_SIZE=$(du -sh .git | awk '{print $1}')
    log "SUCCESS" "Repository cleanup complete!"
    log "INFO" "Repository size before: $INITIAL_SIZE"
    log "INFO" "Repository size after:  $FINAL_SIZE"
fi

log "WARN" "IMPORTANT: This script has modified git history."
log "WARN" "All team members should run the following commands:"
log "INFO" ""
log "INFO" "  git fetch --all"
log "INFO" "  git reset --hard origin/$TARGET_BRANCH"
log "INFO" ""
log "INFO" "Or preferably, clone a fresh copy of the repository."

# Calculate execution time
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))
log "INFO" "Script executed in $EXECUTION_TIME seconds"
log "INFO" "Detailed log available in: $LOG_FILE"