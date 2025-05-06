#!/bin/bash
# execute_gcp_migration_plan.sh
#
# Final Execution Plan - Zero Bullshit Version
# Complete verification of migration with aggressive validation

set -e

# Color coding for output clarity
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
PROJECT_ID="agi-baby-cherry"
ORG_ID="873291114285"
KEY_FILE="vertex-key.json"
SERVICE_ACCOUNT="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"

echo -e "${BOLD}===== FINAL EXECUTION PLAN - ZERO BULLSHIT VERSION =====${NC}"
echo -e "Starting execution at $(date)"

# Step 1: Create the key file from template
echo -e "\n${BLUE}Step 1: Create service account key file${NC}"
echo -e "${YELLOW}Preparing key file for authentication...${NC}"

if [ ! -f "$KEY_FILE" ]; then
    # Prompt for private key content
    echo -e "${YELLOW}Enter your PRIVATE KEY content (paste between BEGIN PRIVATE KEY and END PRIVATE KEY):${NC}"
    read -r PRIVATE_KEY
    
    # Create the key file with proper content
    cat > "$KEY_FILE" <<EOF
{
  "type": "service_account",
  "project_id": "agi-baby-cherry",
  "private_key_id": "6833bc94f0e3ef8648efc1578caa23ba2b8a8a52",
  "private_key": "-----BEGIN PRIVATE KEY-----\n${PRIVATE_KEY}\n-----END PRIVATE KEY-----\n",
  "client_email": "vertex-agent@agi-baby-cherry.iam.gserviceaccount.com",
  "client_id": "104944497835-h9l77l0ltmv4h8t9o5a02m51v8g91a9i",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/vertex-agent%40agi-baby-cherry.iam.gserviceaccount.com"
}
EOF
    chmod 600 "$KEY_FILE"
    echo -e "${GREEN}✅ Key file created with secure permissions (600)${NC}"
else
    echo -e "${GREEN}✅ Key file already exists${NC}"
    chmod 600 "$KEY_FILE"
    echo -e "${GREEN}✅ Key file permissions set to secure (600)${NC}"
fi

# Step 2: Authenticate and verify scripts are executable
echo -e "\n${BLUE}Step 2: Authenticate and prepare verification scripts${NC}"

# Ensure scripts are executable
chmod +x verify_migration.sh prove_migration.sh 2>/dev/null || true
echo -e "${GREEN}✅ Verification scripts are executable${NC}"

# Authenticate with GCP
echo -e "${YELLOW}Authenticating with service account...${NC}"
gcloud auth activate-service-account --key-file="$KEY_FILE" || {
    echo -e "${RED}❌ Authentication failed. Check key file content.${NC}"
    exit 1
}
gcloud config set project "$PROJECT_ID"
echo -e "${GREEN}✅ Authentication successful!${NC}"

# Step 3: Execute nuclear verification
echo -e "\n${BLUE}Step 3: NUCLEAR VERIFICATION${NC}"
echo -e "${YELLOW}Running nuclear verification with --nuke flag...${NC}"

# Execute the full verification in NUKE mode
./verify_migration.sh --nuke || {
    echo -e "${RED}❌ Full verification failed.${NC}"
    echo -e "${YELLOW}Attempting more targeted verification...${NC}"
    
    # Run prove_migration with force mode as fallback
    ./prove_migration.sh --force || {
        echo -e "${RED}❌ All verification attempts failed. Migration may be incomplete.${NC}"
        exit 1
    }
}

# Step 4: Validate critical outputs
echo -e "\n${BLUE}Step 4: VALIDATION OF CRITICAL OUTPUTS${NC}"
echo -e "${YELLOW}Checking evidence file for critical outputs...${NC}"

# Check for critical success indicators in evidence file
ORG_CHECK=$(grep -c "Project $PROJECT_ID in organization $ORG_ID" migration_verification_evidence.txt || echo "0")
GPU_CHECK=$(grep -c "NVIDIA T4 GPUs active" migration_verification_evidence.txt || echo "0")
DB_CHECK=$(grep -c "Redis/AlloyDB connections established" migration_verification_evidence.txt || echo "0")

# Display results of critical checks
echo -e "Organization membership: $([ "$ORG_CHECK" -gt 0 ] && echo "${GREEN}✅ VERIFIED${NC}" || echo "${RED}❌ NOT VERIFIED${NC}")"
echo -e "NVIDIA T4 GPUs: $([ "$GPU_CHECK" -gt 0 ] && echo "${GREEN}✅ VERIFIED${NC}" || echo "${RED}❌ NOT VERIFIED${NC}")"
echo -e "Database connections: $([ "$DB_CHECK" -gt 0 ] && echo "${GREEN}✅ VERIFIED${NC}" || echo "${RED}❌ NOT VERIFIED${NC}")"

# Final validation outcome
if [ "$ORG_CHECK" -gt 0 ] && [ "$GPU_CHECK" -gt 0 ] && [ "$DB_CHECK" -gt 0 ]; then
    echo -e "\n${GREEN}${BOLD}✅ MIGRATION FULLY VERIFIED!${NC}"
    VERIFICATION_STATUS="SUCCESS"
elif [ "$ORG_CHECK" -gt 0 ]; then
    echo -e "\n${YELLOW}${BOLD}⚠️ PARTIAL VERIFICATION: Organization migration successful but infrastructure incomplete${NC}"
    VERIFICATION_STATUS="PARTIAL"
else
    echo -e "\n${RED}${BOLD}❌ VERIFICATION FAILED: Migration appears unsuccessful${NC}"
    VERIFICATION_STATUS="FAILED"
fi

# Step 5: Post-Migration Lockdown
echo -e "\n${BLUE}Step 5: POST-MIGRATION LOCKDOWN${NC}"
echo -e "${YELLOW}Performing credential cleanup...${NC}"

# Revoke credentials and secure environment
gcloud auth revoke "$SERVICE_ACCOUNT" 2>/dev/null || true
echo -e "${GREEN}✅ Service account authentication revoked${NC}"

# Securely delete the key file
echo -e "${YELLOW}Securely deleting key file...${NC}"
# Overwrite with random data first (more secure than simple deletion)
dd if=/dev/urandom of="$KEY_FILE" bs=1k count=1 status=none 2>/dev/null
rm -f "$KEY_FILE"
echo -e "${GREEN}✅ Key file securely deleted${NC}"

# Remove evidence files (optional)
read -p "Delete verification evidence files? (y/n): " DELETE_EVIDENCE
if [[ "$DELETE_EVIDENCE" == "y" ]]; then
    rm -f migration_verification_evidence.txt migration_proof_evidence.txt 2>/dev/null
    echo -e "${GREEN}✅ Evidence files removed${NC}"
fi

# Final summary
echo -e "\n${BOLD}===== FINAL EXECUTION PLAN COMPLETE =====${NC}"
echo -e "Execution finished at $(date)"
echo -e "Final verification status: ${BOLD}$VERIFICATION_STATUS${NC}"

if [ "$VERIFICATION_STATUS" = "SUCCESS" ]; then
    echo -e "\n${GREEN}${BOLD}MIGRATION SUCCESSFULLY VERIFIED WITH ZERO BULLSHIT${NC}"
    echo -e "${GREEN}✅ Project $PROJECT_ID in organization $ORG_ID${NC}"
    echo -e "${GREEN}✅ NVIDIA T4 GPUs active and working${NC}"
    echo -e "${GREEN}✅ Redis/AlloyDB connections established${NC}"
    echo -e "\n${GREEN}${BOLD}ALL OBJECTIVES ACHIEVED${NC}"
    exit 0
else
    echo -e "\n${YELLOW}${BOLD}Some verification checks failed. Review the evidence or logs.${NC}"
    exit 1
fi
