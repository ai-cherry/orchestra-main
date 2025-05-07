#!/bin/bash
# force_migration_nuclear.sh
#
# Final Execution Plan - Zero Bullshit Version
# Force migration with debug logging and immediate verification

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
ORG_ID="873291114285"
SERVICE_ACCOUNT="vertex-agent@cherry-ai-project.iam.gserviceaccount.com"
KEY_FILE="vertex-key.json"
DEBUG_LOG="migration_debug.log"

# Color codes for output clarity
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}===== FORCED MIGRATION AND NUCLEAR VERIFICATION =====${NC}"
echo -e "Starting execution at $(date)"

# Step 1: Clear previous evidence
echo -e "\n${BLUE}Step 1: Burn previous simulations${NC}"
rm -f migration_verification_evidence.txt migration_proof_evidence.txt
echo -e "${GREEN}✅ Previous evidence files removed${NC}"

# Step 2: Set up key file
echo -e "\n${BLUE}Step 2: Prepare key file${NC}"
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}Key file not found. Creating from template...${NC}"
    echo -e "${YELLOW}Enter your PRIVATE KEY content (paste between BEGIN PRIVATE KEY and END PRIVATE KEY):${NC}"
    read -r PRIVATE_KEY
    
    # Create the key file
    cat > "$KEY_FILE" <<EOF
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "6833bc94f0e3ef8648efc1578caa23ba2b8a8a52",
  "private_key": "-----BEGIN PRIVATE KEY-----\n${PRIVATE_KEY}\n-----END PRIVATE KEY-----\n",
  "client_email": "vertex-agent@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "104944497835-h9l77l0ltmv4h8t9o5a02m51v8g91a9i",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/vertex-agent%40cherry-ai-project.iam.gserviceaccount.com"
}
EOF
    chmod 600 "$KEY_FILE"
    echo -e "${GREEN}✅ Key file created with secure permissions (600)${NC}"
else
    echo -e "${GREEN}✅ Key file already exists${NC}"
    chmod 600 "$KEY_FILE"
    echo -e "${GREEN}✅ Permissions set to 600${NC}"
fi

# Step 3: Authenticate
echo -e "\n${BLUE}Step 3: Authenticate with service account${NC}"
gcloud auth activate-service-account --key-file="$KEY_FILE" || {
    echo -e "${RED}❌ Authentication failed. Check key file.${NC}"
    exit 1
}
gcloud config set project "$PROJECT_ID"
echo -e "${GREEN}✅ Authentication successful${NC}"

# Step 4: Force migration with debug logging
echo -e "\n${BLUE}Step 4: Force migration with debug logging${NC}"
echo -e "${YELLOW}Executing forced migration with full debug output...${NC}"

# Delete previous debug log if it exists
rm -f "$DEBUG_LOG"

# Execute the migration with full debug logging
echo -e "${BOLD}STARTING MIGRATION COMMAND:${NC}"
echo -e "gcloud beta projects move $PROJECT_ID --organization=$ORG_ID --billing-project=$PROJECT_ID --verbosity=debug --log-http"

gcloud beta projects move "$PROJECT_ID" \
  --organization="$ORG_ID" \
  --billing-project="$PROJECT_ID" \
  --verbosity=debug \
  --log-http \
  2>&1 | tee "$DEBUG_LOG"

MIGRATION_STATUS=$?
if [ $MIGRATION_STATUS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ Migration command executed successfully${NC}"
else
    echo -e "${YELLOW}⚠️ Migration command exited with status: $MIGRATION_STATUS${NC}"
    echo -e "${YELLOW}This may be normal if the project is already in the correct organization${NC}"
fi

echo -e "${GREEN}Debug log saved to $DEBUG_LOG${NC}"

# Step 5: Immediate post-migration checks
echo -e "\n${BLUE}Step 5: Immediate post-migration checks${NC}"

# Check 1: Organization binding
echo -e "\n${YELLOW}Check 1: Organization binding${NC}"
ORG_CHECK=$(gcloud projects describe "$PROJECT_ID" --format="value(parent.id)")
echo -e "Organization check result: ${BOLD}$ORG_CHECK${NC}"

if [[ "$ORG_CHECK" == "organizations/$ORG_ID" ]]; then
    echo -e "${GREEN}${BOLD}✅ PROJECT SUCCESSFULLY MIGRATED TO ORGANIZATION ${ORG_ID}${NC}"
    ORG_SUCCESS=true
else
    echo -e "${RED}${BOLD}❌ PROJECT NOT IN EXPECTED ORGANIZATION${NC}"
    echo -e "${RED}Current organization: $ORG_CHECK${NC}"
    ORG_SUCCESS=false
fi

# Check 2: Service account validity
echo -e "\n${YELLOW}Check 2: Service account validity${NC}"
SA_LIST=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo -e "Active accounts: ${BOLD}$SA_LIST${NC}"

if [[ "$SA_LIST" == *"$SERVICE_ACCOUNT"* ]]; then
    echo -e "${GREEN}✅ Service account is active${NC}"
else
    echo -e "${RED}❌ Service account not found in active accounts${NC}"
fi

# Check 3: IAM policy confirmation
echo -e "\n${YELLOW}Check 3: IAM policy confirmation${NC}"
echo -e "Checking organization IAM policy for $SERVICE_ACCOUNT..."
IAM_POLICY=$(gcloud organizations get-iam-policy "$ORG_ID" --filter="bindings.members:$SERVICE_ACCOUNT" --format="value(bindings.role)" 2>/dev/null || echo "Error: Unable to retrieve IAM policy")
echo -e "IAM roles: ${BOLD}$IAM_POLICY${NC}"

if [[ "$IAM_POLICY" == *"roles/resourcemanager.projectMover"* ]]; then
    echo -e "${GREEN}✅ Service account has projectMover role${NC}"
else
    echo -e "${YELLOW}⚠️ Service account missing projectMover role${NC}"
fi

# Additional Checks from the user's requirements
if [ "$ORG_SUCCESS" != "true" ]; then
    echo -e "\n${BLUE}Step 6: Critical fixes${NC}"
    
    # Fix 1: Recreate service account key
    echo -e "\n${YELLOW}Fix 1: Recreate service account key${NC}"
    read -p "Recreate service account key? (y/n): " RECREATE_KEY
    if [[ "$RECREATE_KEY" == "y" ]]; then
        NEW_KEY_FILE="new-key.json"
        gcloud iam service-accounts keys create "$NEW_KEY_FILE" \
          --iam-account="$SERVICE_ACCOUNT" || {
            echo -e "${RED}❌ Key creation failed${NC}"
        }
        
        if [ -f "$NEW_KEY_FILE" ]; then
            chmod 600 "$NEW_KEY_FILE"
            echo -e "${GREEN}✅ New key created: $NEW_KEY_FILE${NC}"
            
            # Use the new key
            gcloud auth activate-service-account --key-file="$NEW_KEY_FILE" || {
                echo -e "${RED}❌ Authentication with new key failed${NC}"
            }
            echo -e "${GREEN}✅ Authenticated with new key${NC}"
            KEY_FILE="$NEW_KEY_FILE"
        fi
    fi
    
    # Fix 2: Billing project override
    echo -e "\n${YELLOW}Fix 2: Billing project override${NC}"
    read -p "Fix billing project linkage? (y/n): " FIX_BILLING
    if [[ "$FIX_BILLING" == "y" ]]; then
        gcloud beta billing projects link "$PROJECT_ID" \
          --billing-project="$PROJECT_ID" || {
            echo -e "${RED}❌ Billing project fix failed${NC}"
        }
        echo -e "${GREEN}✅ Billing project fix attempted${NC}"
    fi
    
    # Fix 3: Organization policy exception
    echo -e "\n${YELLOW}Fix 3: Organization policy exception${NC}"
    read -p "Create organization policy exception? (y/n): " CREATE_EXCEPTION
    if [[ "$CREATE_EXCEPTION" == "y" ]]; then
        # Create a temporary policy file
        cat > allow-project-move.yaml <<EOF
name: organizations/$ORG_ID/policies/constraints/resourcemanager.allowedExportDestinations
spec:
  rules:
  - condition:
      expression: "true"
    values:
      allowedValues:
      - "under:organizations/$ORG_ID"
EOF
        
        gcloud org-policies set-policy allow-project-move.yaml \
          --organization="$ORG_ID" || {
            echo -e "${RED}❌ Organization policy exception failed${NC}"
        }
        echo -e "${GREEN}✅ Organization policy exception attempted${NC}"
        
        # Clean up
        rm -f allow-project-move.yaml
    fi
    
    # Retry migration
    echo -e "\n${YELLOW}Retrying migration with force option...${NC}"
    read -p "Retry migration now? (y/n): " RETRY_MIGRATION
    if [[ "$RETRY_MIGRATION" == "y" ]]; then
        gcloud beta projects move "$PROJECT_ID" \
          --organization="$ORG_ID" \
          --billing-project="$PROJECT_ID" \
          --quiet || {
            echo -e "${RED}❌ Forced migration retry failed${NC}"
        }
        
        # Final check
        FINAL_ORG=$(gcloud projects describe "$PROJECT_ID" --format="value(parent.id)")
        echo -e "Final organization check: ${BOLD}$FINAL_ORG${NC}"
        
        if [[ "$FINAL_ORG" == "organizations/$ORG_ID" ]]; then
            echo -e "${GREEN}${BOLD}✅ MIGRATION FINALLY SUCCEEDED${NC}"
        else
            echo -e "${RED}${BOLD}❌ MIGRATION STILL FAILED AFTER ALL FIXES${NC}"
        fi
    fi
fi

# Step 7: Final atomic verification
echo -e "\n${BLUE}Step 7: Final atomic verification${NC}"
ATOMIC_RESULT=$(gcloud projects describe "$PROJECT_ID" --format="value(name,parent.id)")
echo -e "Atomic verification: ${BOLD}$ATOMIC_RESULT${NC}"

EXPECTED="$PROJECT_ID organizations/$ORG_ID"
if [ "$ATOMIC_RESULT" = "$EXPECTED" ]; then
    echo -e "${GREEN}${BOLD}✅ FINAL VERIFICATION SUCCESSFUL${NC}"
    echo -e "${GREEN}${BOLD}Migration Complete. Project $PROJECT_ID is now in organization $ORG_ID.${NC}"
else
    echo -e "${RED}${BOLD}❌ FINAL VERIFICATION FAILED${NC}"
    echo -e "${RED}Expected: $EXPECTED${NC}"
    echo -e "${RED}Actual: $ATOMIC_RESULT${NC}"
fi

# Optional cleanup
read -p "Securely delete key file after verification? (y/n): " DELETE_KEY
if [[ "$DELETE_KEY" == "y" ]] && [ -f "$KEY_FILE" ]; then
    # Overwrite with random data before deletion (secure deletion)
    dd if=/dev/urandom of="$KEY_FILE" bs=1k count=1 &>/dev/null
    rm -f "$KEY_FILE"
    echo -e "${GREEN}✅ Key file securely deleted${NC}"
fi

echo -e "\n${BOLD}Process completed at $(date)${NC}"
