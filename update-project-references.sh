#!/bin/bash
# Script to update all references from old GCP project ID to new one
# across the codebase

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
OLD_PROJECT="cherry-ai-project"
NEW_PROJECT="cherry-ai-project"
BACKUP_DIR="project_id_updates_backup_$(date '+%Y%m%d_%H%M%S')"
LOG_FILE="project_id_update_$(date '+%Y%m%d_%H%M%S').log"
EXCLUDED_DIRS=".git node_modules .terraform tmp backup_configs"
EXCLUDED_FILES="*.tfstate* *.lock.hcl"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Print header
echo -e "${BLUE}=============================================================${NC}"
echo -e "${BLUE}${BOLD}   GCP Project ID Migration: $OLD_PROJECT → $NEW_PROJECT   ${NC}"
echo -e "${BLUE}=============================================================${NC}"

echo -e "\n${YELLOW}This script will update all references from $OLD_PROJECT to $NEW_PROJECT${NC}"
echo -e "${YELLOW}A backup of changed files will be created in ${BACKUP_DIR}${NC}"
echo -e "${YELLOW}A log of all changes will be written to ${LOG_FILE}${NC}"

# Prompt for confirmation
read -p "Do you want to continue? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Operation aborted.${NC}"
    exit 1
fi

# Create exclusion pattern for find command
EXCLUDE_PATTERN=""
for dir in $EXCLUDED_DIRS; do
    EXCLUDE_PATTERN="$EXCLUDE_PATTERN -not -path '*/$dir/*'"
done

for file in $EXCLUDED_FILES; do
    EXCLUDE_PATTERN="$EXCLUDE_PATTERN -not -name '$file'"
done

# Function to log messages
log() {
    local msg="$1"
    echo "$msg" | tee -a "$LOG_FILE"
}

# Log start time
log "Started migration at $(date '+%Y-%m-%d %H:%M:%S')"
log "Searching for files containing '$OLD_PROJECT'..."

# Find all files containing the old project ID, excluding specified directories and files
# shellcheck disable=SC2086
FILES_TO_CHECK=$(eval "find . -type f -not -path '*/\.*' $EXCLUDE_PATTERN -exec grep -l '$OLD_PROJECT' {} \;")

if [ -z "$FILES_TO_CHECK" ]; then
    log "No files found containing '$OLD_PROJECT'"
    echo -e "${GREEN}No files found containing '$OLD_PROJECT'. Nothing to do.${NC}"
    exit 0
fi

# Count files to process
FILE_COUNT=$(echo "$FILES_TO_CHECK" | wc -l)
log "Found $FILE_COUNT files containing '$OLD_PROJECT'"
echo -e "${YELLOW}Found $FILE_COUNT files containing '$OLD_PROJECT'${NC}"

# Process files
COUNTER=0
for file in $FILES_TO_CHECK; do
    # Update progress counter
    COUNTER=$((COUNTER + 1))
    echo -e "${BLUE}[$COUNTER/$FILE_COUNT] Processing ${file}${NC}"
    
    # Make backup of the file
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    cp "$file" "$BACKUP_DIR/$file"
    
    # Count occurrences before replacement
    OCCURRENCES=$(grep -o "$OLD_PROJECT" "$file" | wc -l)
    
    # Skip binary files
    if file "$file" | grep -q "binary"; then
        log "SKIPPED (binary): $file"
        echo -e "${YELLOW}  Skipping binary file${NC}"
        continue
    fi
    
    # Handle service account emails specially
    if grep -q "@$OLD_PROJECT\.iam\.gserviceaccount\.com" "$file"; then
        # First backup for email changes specifically
        cp "$file" "$BACKUP_DIR/${file}.email_backup"
        
        # Update service account emails
        sed -i "s/@$OLD_PROJECT\.iam\.gserviceaccount\.com/@$NEW_PROJECT\.iam\.gserviceaccount\.com/g" "$file"
        
        EMAIL_CHANGES=$(grep -o "@$NEW_PROJECT\.iam\.gserviceaccount\.com" "$file" | wc -l)
        log "Updated $EMAIL_CHANGES service account email references in $file"
        echo -e "${GREEN}  Updated $EMAIL_CHANGES service account email references${NC}"
    fi
    
    # Handle bucket names specially
    if grep -q "gs://$OLD_PROJECT" "$file"; then
        # Backup for bucket changes
        cp "$file" "$BACKUP_DIR/${file}.bucket_backup"
        
        # Update GCS bucket references
        sed -i "s/gs:\/\/$OLD_PROJECT-/gs:\/\/$NEW_PROJECT-/g" "$file"
        
        BUCKET_CHANGES=$(grep -o "gs://$NEW_PROJECT-" "$file" | wc -l)
        log "Updated $BUCKET_CHANGES GCS bucket references in $file"
        echo -e "${GREEN}  Updated $BUCKET_CHANGES GCS bucket references${NC}"
    fi
    
    # Handle Artifact Registry references
    if grep -q "$OLD_PROJECT\/[^\/]*\/[^\/]*:" "$file"; then
        # Backup for Artifact Registry changes
        cp "$file" "$BACKUP_DIR/${file}.ar_backup"
        
        # Update Artifact Registry references
        sed -i "s/\([^-]\)$OLD_PROJECT\/\([^\/]*\/[^\/]*:\)/\1$NEW_PROJECT\/\2/g" "$file"
        
        AR_CHANGES=$(grep -o "$NEW_PROJECT/[^/]*/[^/]*:" "$file" | wc -l)
        log "Updated $AR_CHANGES Artifact Registry references in $file"
        echo -e "${GREEN}  Updated $AR_CHANGES Artifact Registry references${NC}"
    fi
    
    # General replacement for other references
    sed -i "s/\([^-@/]\)$OLD_PROJECT\([^-a-zA-Z0-9]\)/\1$NEW_PROJECT\2/g" "$file"
    
    # Count occurrences after replacement
    NEW_OCCURRENCES=$(grep -o "$OLD_PROJECT" "$file" | wc -l)
    CHANGES=$((OCCURRENCES - NEW_OCCURRENCES))
    
    # Log the changes
    if [ $CHANGES -gt 0 ]; then
        log "Updated $CHANGES references in $file"
        echo -e "${GREEN}  Updated $CHANGES references${NC}"
    else
        REMAINING=$(grep -o "$OLD_PROJECT" "$file" | wc -l)
        if [ $REMAINING -gt 0 ]; then
            log "MANUAL REVIEW NEEDED: $REMAINING references still remain in $file"
            echo -e "${RED}  MANUAL REVIEW NEEDED: $REMAINING references still remain${NC}"
            
            # Extract lines for manual review
            LINE_NUMBERS=$(grep -n "$OLD_PROJECT" "$file" | cut -d':' -f1)
            for line in $LINE_NUMBERS; do
                CONTEXT=$(grep -A 2 -B 2 -n "$OLD_PROJECT" "$file" | grep -F "${line}:")
                log "  Line $CONTEXT"
                echo -e "${YELLOW}  Line: $CONTEXT${NC}"
            done
        fi
    fi
done

# Log completion
log "Completed migration at $(date '+%Y-%m-%d %H:%M:%S')"
log "Total files processed: $FILE_COUNT"

echo -e "\n${GREEN}${BOLD}Project ID migration completed!${NC}"
echo -e "${YELLOW}A backup of all modified files is available in ${BACKUP_DIR}${NC}"
echo -e "${YELLOW}A log of all changes is available in ${LOG_FILE}${NC}"
echo -e "\n${RED}${BOLD}IMPORTANT:${NC} Some files may require manual review. Check the log for 'MANUAL REVIEW NEEDED' entries."
echo -e "${RED}The script attempted to handle special cases, but some complex patterns may need manual adjustment.${NC}"
echo -e "\n${BLUE}Next steps:${NC}"
echo -e "1. Review the changes made (git diff)"
echo -e "2. Check for any remaining occurrences: grep -r '$OLD_PROJECT' --include='*.{tf,sh,yml,yaml,md,js,py}' ."
echo -e "3. Test the changes in a development environment"
echo -e "4. Commit the changes: git commit -am 'Update GCP project ID references from $OLD_PROJECT to $NEW_PROJECT'"
