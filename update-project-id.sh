#!/bin/bash
# Script to update all references from cherry-ai-project to cherry-ai-project
# This script will update files in-place

set -e  # Exit on any error

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m"  # No Color

# Configuration
OLD_PROJECT="cherry-ai-project"
NEW_PROJECT="cherry-ai-project"
OLD_REGION="us-west4"
NEW_REGION="us-west4"

# Print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print warning message
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Ask for confirmation
confirm() {
    read -p "$1 (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    return 0
}

section "Project ID Migration Script"
echo "This script will update all references from '$OLD_PROJECT' to '$NEW_PROJECT'"
echo "and from '$OLD_REGION' to '$NEW_REGION' across the codebase."
echo ""
echo "Files will be modified in-place. Make sure you have a backup or commit your changes before proceeding."
echo ""

if ! confirm "Do you want to proceed?"; then
    exit 0
fi

# Create a backup directory
BACKUP_DIR="project_id_migration_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
success "Created backup directory: $BACKUP_DIR"

# Find all files containing the old project ID and make backups
section "Creating Backups"
echo "Finding files containing '$OLD_PROJECT'..."
FILES_TO_UPDATE=$(grep -r --include="*.py" --include="*.sh" --include="*.yml" --include="*.yaml" --include="*.tf" --include="*.md" --include="*.json" --include="*.js" "$OLD_PROJECT" . | cut -d: -f1 | sort | uniq)

# Count files to update
FILE_COUNT=$(echo "$FILES_TO_UPDATE" | wc -l)
echo "Found $FILE_COUNT files to update."

# Create backups
for file in $FILES_TO_UPDATE; do
    # Skip backup directory itself
    if [[ "$file" == ./$BACKUP_DIR/* ]]; then
        continue
    fi
    
    # Create directory structure in backup
    backup_file="$BACKUP_DIR/$file"
    mkdir -p "$(dirname "$backup_file")"
    
    # Copy file to backup
    cp "$file" "$backup_file"
    echo "Backed up: $file"
done

success "Created backups of all files to be modified"

# Update files
section "Updating Files"
echo "Replacing '$OLD_PROJECT' with '$NEW_PROJECT' in all files..."

# Different patterns to replace
patterns=(
    # Basic project ID
    "s/$OLD_PROJECT/$NEW_PROJECT/g"
    
    # Service account emails
    "s/@$OLD_PROJECT\.iam\.gserviceaccount\.com/@$NEW_PROJECT\.iam\.gserviceaccount\.com/g"
    
    # GCS bucket references
    "s/gs:\/\/$OLD_PROJECT-/gs:\/\/$NEW_PROJECT-/g"
    
    # Docker image references
    "s/us-docker\.pkg\.dev\/$OLD_PROJECT\//us-docker\.pkg\.dev\/$NEW_PROJECT\//g"
    "s/us-west2-docker\.pkg\.dev\/$OLD_PROJECT\//us-west2-docker\.pkg\.dev\/$NEW_PROJECT\//g"
    
    # Region updates
    "s/$OLD_REGION/$NEW_REGION/g"
)

# Apply all patterns to each file
for file in $FILES_TO_UPDATE; do
    # Skip backup directory itself
    if [[ "$file" == ./$BACKUP_DIR/* ]]; then
        continue
    fi
    
    echo "Updating: $file"
    for pattern in "${patterns[@]}"; do
        sed -i "$pattern" "$file"
    done
done

success "Updated all references from '$OLD_PROJECT' to '$NEW_PROJECT'"

section "Verification"
echo "Checking for any remaining references to '$OLD_PROJECT'..."
REMAINING=$(grep -r --include="*.py" --include="*.sh" --include="*.yml" --include="*.yaml" --include="*.tf" --include="*.md" --include="*.json" --include="*.js" "$OLD_PROJECT" . | grep -v "$BACKUP_DIR" || echo "")

if [ -n "$REMAINING" ]; then
    warning "Some references to '$OLD_PROJECT' still remain:"
    echo "$REMAINING" | head -n 10
    if [ $(echo "$REMAINING" | wc -l) -gt 10 ]; then
        echo "... and more (showing first 10 only)"
    fi
    echo ""
    echo "You may need to update these manually or run the script again with additional patterns."
else
    success "No remaining references to '$OLD_PROJECT' found!"
fi

section "Next Steps"
echo "1. Review the changes to ensure they are correct"
echo "2. Test the application with the new project ID"
echo "3. Update any external references (e.g., documentation, CI/CD pipelines)"
echo ""
echo "If you need to revert changes, the original files are in: $BACKUP_DIR"

success "Project ID migration completed!"