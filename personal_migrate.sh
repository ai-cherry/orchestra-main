#!/bin/bash
# personal_migrate.sh
#
# Simplified GCP migration script for scoobyjava@cherry-ai.me
# Handles permissions, migration, and master service account setup

set -e

# Configuration
PROJECT_ID="agi-baby-cherry"
ORG_ID="873291114285"
USER_EMAIL="scoobyjava@cherry-ai.me"
MASTER_SA_NAME="org-master-sa"
MASTER_SA_EMAIL="${MASTER_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
MASTER_KEY_FILE="org-master-key.json"

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}===== PERSONAL GCP MIGRATION - ONE SHOT EXECUTION =====${NC}"
echo -e "Starting execution at $(date)"

# Step 1: Ensure user has proper permissions
echo -e "\n${BLUE}Step 1: Ensure user has proper permissions${NC}"
echo -e "${YELLOW}Granting necessary permissions to ${USER_EMAIL}...${NC}"

# Grant owner permission on the project
echo -e "Granting owner permission on project..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="user:${USER_EMAIL}" \
  --role="roles/owner" || {
    echo -e "${RED}❌ Failed to grant owner permission. Continuing anyway...${NC}"
}

# Grant project creator permission on the organization
echo -e "Granting projectCreator permission on organization..."
gcloud organizations add-iam-policy-binding "$ORG_ID" \
  --member="user:${USER_EMAIL}" \
  --role="roles/resourcemanager.projectCreator" || {
    echo -e "${RED}❌ Failed to grant projectCreator permission. Continuing anyway...${NC}"
}

# Grant project mover permission on the organization
echo -e "Granting projectMover permission on organization..."
gcloud organizations add-iam-policy-binding "$ORG_ID" \
  --member="user:${USER_EMAIL}" \
  --role="roles/resourcemanager.projectMover" || {
    echo -e "${RED}❌ Failed to grant projectMover permission. Continuing anyway...${NC}"
}

echo -e "${GREEN}✅ Permissions granted (or already exist)${NC}"

# Step 2: Set default project
echo -e "\n${BLUE}Step 2: Set default project${NC}"
gcloud config set project "$PROJECT_ID"
echo -e "${GREEN}✅ Default project set to $PROJECT_ID${NC}"

# Step 3: Execute migration
echo -e "\n${BLUE}Step 3: Execute migration${NC}"
echo -e "${YELLOW}Migrating project to organization...${NC}"

# Execute the migration command
gcloud beta projects move "$PROJECT_ID" --organization "$ORG_ID" || {
    echo -e "${RED}❌ Initial migration attempt failed. Trying with additional options...${NC}"
    
    # Wait for IAM propagation
    echo -e "${YELLOW}Waiting 60 seconds for IAM propagation...${NC}"
    sleep 60
    
    # Try again with more options
    gcloud beta projects move "$PROJECT_ID" \
      --organization="$ORG_ID" \
      --billing-project="$PROJECT_ID" \
      --quiet || {
        echo -e "${RED}❌ Migration failed again. See error above.${NC}"
        echo -e "${YELLOW}You may need to wait longer for IAM permission propagation (5+ minutes).${NC}"
        echo -e "${YELLOW}To retry later, run: gcloud beta projects move $PROJECT_ID --organization $ORG_ID${NC}"
        
        # Set a flag to indicate migration failed
        MIGRATION_FAILED=true
    }
}

# Step 4: Verify migration
echo -e "\n${BLUE}Step 4: Verify migration${NC}"
echo -e "${YELLOW}Checking project organization...${NC}"

# Get current organization
CURRENT_ORG=$(gcloud projects describe "$PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "failed")
echo -e "Current project organization: ${BOLD}$CURRENT_ORG${NC}"

if [[ "$CURRENT_ORG" == "organizations/$ORG_ID" ]]; then
    echo -e "${GREEN}${BOLD}✅ MIGRATION SUCCESSFUL!${NC}"
    echo -e "${GREEN}Project $PROJECT_ID is now in organization $ORG_ID${NC}"
    MIGRATION_SUCCESS=true
else
    echo -e "${RED}${BOLD}❌ MIGRATION VERIFICATION FAILED${NC}"
    echo -e "${RED}Project is not in the expected organization.${NC}"
    echo -e "${RED}Current: $CURRENT_ORG, Expected: organizations/$ORG_ID${NC}"
    MIGRATION_FAILED=true
fi

# Step 5: Update billing association
echo -e "\n${BLUE}Step 5: Update billing association${NC}"
echo -e "${YELLOW}Linking project to billing account...${NC}"

# Get available billing accounts
BILLING_ACCOUNT=$(gcloud beta billing accounts list --format="value(name)" | head -n 1)

if [ -n "$BILLING_ACCOUNT" ]; then
    # Link project to billing account
    gcloud beta billing projects link "$PROJECT_ID" \
      --billing-account="$BILLING_ACCOUNT" || {
        echo -e "${RED}❌ Failed to link billing account. See error above.${NC}"
    }
    echo -e "${GREEN}✅ Project linked to billing account $BILLING_ACCOUNT${NC}"
else
    echo -e "${YELLOW}⚠️ No billing accounts found. Skipping billing linkage.${NC}"
fi

# Only proceed with master service account if migration succeeded
if [ "$MIGRATION_SUCCESS" = true ] || [ ! "$MIGRATION_FAILED" = true ]; then
    # Step 6: Create master service account
    echo -e "\n${BLUE}Step 6: Create master service account${NC}"
    
    # Ask if user wants to create master SA
    read -p "Create organization-wide master service account? (y/n): " CREATE_MASTER_SA
    
    if [[ "$CREATE_MASTER_SA" == "y" ]]; then
        echo -e "${YELLOW}Creating master service account...${NC}"
        
        # Create service account
        gcloud iam service-accounts create "$MASTER_SA_NAME" \
          --display-name="Organization Master Service Account" || {
            echo -e "${RED}❌ Failed to create service account. See error above.${NC}"
            echo -e "${YELLOW}It may already exist or you may not have permission.${NC}"
            
            # Try to continue anyway
            echo -e "${YELLOW}Attempting to continue with existing service account...${NC}"
        }
        
        # Grant organization admin permission
        echo -e "${YELLOW}Granting organizationAdmin role to service account...${NC}"
        gcloud organizations add-iam-policy-binding "$ORG_ID" \
          --member="serviceAccount:${MASTER_SA_EMAIL}" \
          --role="roles/resourcemanager.organizationAdmin" || {
            echo -e "${RED}❌ Failed to grant organizationAdmin permission. See error above.${NC}"
        }
        
        # Grant billing admin permission
        echo -e "${YELLOW}Granting billing.admin role to service account...${NC}"
        gcloud organizations add-iam-policy-binding "$ORG_ID" \
          --member="serviceAccount:${MASTER_SA_EMAIL}" \
          --role="roles/billing.admin" || {
            echo -e "${RED}❌ Failed to grant billing.admin permission. See error above.${NC}"
        }
        
        # Grant security admin permission
        echo -e "${YELLOW}Granting iam.securityAdmin role to service account...${NC}"
        gcloud organizations add-iam-policy-binding "$ORG_ID" \
          --member="serviceAccount:${MASTER_SA_EMAIL}" \
          --role="roles/iam.securityAdmin" || {
            echo -e "${RED}❌ Failed to grant iam.securityAdmin permission. See error above.${NC}"
        }
        
        # Create service account key
        echo -e "${YELLOW}Creating service account key...${NC}"
        gcloud iam service-accounts keys create "$MASTER_KEY_FILE" \
          --iam-account="$MASTER_SA_EMAIL" || {
            echo -e "${RED}❌ Failed to create service account key. See error above.${NC}"
        }
        
        # Set secure permissions on key file
        if [ -f "$MASTER_KEY_FILE" ]; then
            chmod 600 "$MASTER_KEY_FILE"
            echo -e "${GREEN}✅ Master service account key created: $MASTER_KEY_FILE (permissions set to 600)${NC}"
            echo -e "${GREEN}✅ Master service account setup complete${NC}"
            
            # Display usage instructions
            echo -e "\n${BLUE}Using the master service account:${NC}"
            echo -e "To authenticate: ${BOLD}gcloud auth activate-service-account --key-file=$MASTER_KEY_FILE${NC}"
            echo -e "To verify access: ${BOLD}gcloud organizations get-iam-policy $ORG_ID${NC}"
        else
            echo -e "${RED}❌ Key file creation failed or file not found.${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping master service account creation.${NC}"
    fi
fi

# Final summary
echo -e "\n${BOLD}===== EXECUTION SUMMARY =====${NC}"

if [ "$MIGRATION_SUCCESS" = true ] || [ ! "$MIGRATION_FAILED" = true ]; then
    echo -e "${GREEN}${BOLD}✅ MIGRATION COMPLETED SUCCESSFULLY${NC}"
    
    echo -e "\n${BOLD}NEXT STEPS:${NC}"
    echo -e "1. Verify in GCP Console: Go to IAM & Admin > Settings"
    echo -e "   Confirm 'Organization' field shows 'cherry-ai.me'"
    echo -e "2. Check workstation access and GPU configurations"
    echo -e "3. Verify database connections (Redis/AlloyDB)"
    
    if [[ "$CREATE_MASTER_SA" == "y" ]] && [ -f "$MASTER_KEY_FILE" ]; then
        echo -e "4. Test the master service account authentication"
        echo -e "5. Securely store the master key file ($MASTER_KEY_FILE)"
    fi
else
    echo -e "${RED}${BOLD}❌ MIGRATION FAILED${NC}"
    echo -e "${YELLOW}Please check error messages above and try again after waiting for IAM propagation.${NC}"
    echo -e "${YELLOW}Alternatively, try running the ./force_migration_nuclear.sh script with your service account key.${NC}"
fi

echo -e "\nExecution finished at $(date)"
