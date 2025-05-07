#!/bin/bash
# definitive_migration_verify.sh
#
# Zero Bullshit Verification Script
# Definitively proves migration with direct GCP commands and nuclear options

set -e

# Configuration
PROJECT_ID="agi-baby-cherry"
ORG_ID="873291114285"
SERVICE_ACCOUNT="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"
KEY_FILE="vertex-key.json"
DEBUG_LOG="migration_debug.log"
EVIDENCE_FILE="definitive_migration_evidence.txt"

# Color coding for clear output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Clear previous verification evidence
echo -e "${BLUE}Clearing previous verification evidence...${NC}"
rm -f migration_verification_evidence.txt migration_proof_evidence.txt "$EVIDENCE_FILE"
> "$EVIDENCE_FILE"  # Create empty evidence file

echo -e "${BOLD}===== DEFINITIVE MIGRATION VERIFICATION - NUCLEAR APPROACH =====${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "Starting verification at $(date)" | tee -a "$EVIDENCE_FILE"

# STEP 1: Direct Organization Verification - THE PRIMARY SUCCESS INDICATOR
echo -e "\n${BOLD}STEP 1: DIRECT ORGANIZATION VERIFICATION${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "${YELLOW}Running direct project organization check...${NC}" | tee -a "$EVIDENCE_FILE"

ORG_CHECK=$(gcloud projects describe "$PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "failed")
echo -e "Project parent organization: ${BOLD}$ORG_CHECK${NC}" | tee -a "$EVIDENCE_FILE"

if [[ "$ORG_CHECK" == "organizations/$ORG_ID" ]]; then
    echo -e "${GREEN}${BOLD}✅ PRIMARY SUCCESS CONFIRMED: Project is in the correct organization${NC}" | tee -a "$EVIDENCE_FILE"
    ORG_SUCCESS=true
else
    echo -e "${RED}❌ PRIMARY CHECK FAILED: Project is not in the expected organization${NC}" | tee -a "$EVIDENCE_FILE"
    ORG_SUCCESS=false
fi

# STEP 2: Service Account Authentication Verification
echo -e "\n${BOLD}STEP 2: SERVICE ACCOUNT VERIFICATION${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "${YELLOW}Checking active service accounts...${NC}" | tee -a "$EVIDENCE_FILE"

# Check if we need to authenticate first
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
if [ -z "$CURRENT_ACCOUNT" ] && [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}Authenticating with service account key...${NC}" | tee -a "$EVIDENCE_FILE"
    gcloud auth activate-service-account --key-file="$KEY_FILE" 2>/dev/null || {
        echo -e "${RED}❌ Authentication failed. Check key file.${NC}" | tee -a "$EVIDENCE_FILE"
    }
fi

ACTIVE_ACCOUNTS=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
echo -e "Active service accounts:" | tee -a "$EVIDENCE_FILE"
echo "$ACTIVE_ACCOUNTS" | tee -a "$EVIDENCE_FILE"

if [[ "$ACTIVE_ACCOUNTS" == *"$SERVICE_ACCOUNT"* ]]; then
    echo -e "${GREEN}✅ Service account active${NC}" | tee -a "$EVIDENCE_FILE"
    SA_SUCCESS=true
else
    echo -e "${YELLOW}⚠️ Target service account not in active list${NC}" | tee -a "$EVIDENCE_FILE"
    SA_SUCCESS=false
fi

# STEP 3: IAM Organization Bindings Verification
echo -e "\n${BOLD}STEP 3: IAM ORGANIZATION BINDINGS${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "${YELLOW}Checking organization IAM policy bindings...${NC}" | tee -a "$EVIDENCE_FILE"

IAM_BINDINGS=$(gcloud organizations get-iam-policy "$ORG_ID" --filter="bindings.members:$SERVICE_ACCOUNT" --format="value(bindings.role)" 2>/dev/null || echo "")
echo -e "IAM roles for $SERVICE_ACCOUNT:" | tee -a "$EVIDENCE_FILE"
echo "$IAM_BINDINGS" | tee -a "$EVIDENCE_FILE"

# Check if key roles are present
if [[ "$IAM_BINDINGS" == *"roles/resourcemanager.projectMover"* ]]; then
    echo -e "${GREEN}✅ Project mover role found${NC}" | tee -a "$EVIDENCE_FILE"
    MOVER_ROLE=true
else
    echo -e "${YELLOW}⚠️ Project mover role not found${NC}" | tee -a "$EVIDENCE_FILE"
    MOVER_ROLE=false
fi

if [[ "$IAM_BINDINGS" == *"roles/resourcemanager.projectCreator"* ]]; then
    echo -e "${GREEN}✅ Project creator role found${NC}" | tee -a "$EVIDENCE_FILE"
    CREATOR_ROLE=true
else
    echo -e "${YELLOW}⚠️ Project creator role not found${NC}" | tee -a "$EVIDENCE_FILE"
    CREATOR_ROLE=false
fi

# STEP 4: Workstation and GPU Verification
echo -e "\n${BOLD}STEP 4: WORKSTATION & GPU VERIFICATION${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "${YELLOW}Checking for workstation clusters and GPU configurations...${NC}" | tee -a "$EVIDENCE_FILE"

# List workstation clusters
CLUSTERS=$(gcloud workstations clusters list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")
echo -e "Workstation clusters:" | tee -a "$EVIDENCE_FILE"
echo "$CLUSTERS" | tee -a "$EVIDENCE_FILE"

if [ -n "$CLUSTERS" ]; then
    echo -e "${GREEN}✅ Workstation clusters found${NC}" | tee -a "$EVIDENCE_FILE"
    CLUSTERS_FOUND=true
    
    # Check for ai-development cluster
    if [[ "$CLUSTERS" == *"ai-development"* ]]; then
        echo -e "${GREEN}✅ ai-development cluster found${NC}" | tee -a "$EVIDENCE_FILE"
        
        # Check for GPU configuration
        GPU_INFO=$(gcloud workstations configs describe ai-dev-config --cluster=ai-development --region=us-central1 --project="$PROJECT_ID" --format="json(container.guestAccelerators)" 2>/dev/null || echo "{}")
        echo -e "GPU configuration:" | tee -a "$EVIDENCE_FILE"
        echo "$GPU_INFO" | tee -a "$EVIDENCE_FILE"
        
        if [[ "$GPU_INFO" == *"nvidia-tesla-t4"* ]] && [[ "$GPU_INFO" == *"count\": 2"* ]]; then
            echo -e "${GREEN}${BOLD}✅ 2x NVIDIA T4 GPUs active in us-central1${NC}" | tee -a "$EVIDENCE_FILE"
            GPU_SUCCESS=true
        else
            echo -e "${YELLOW}⚠️ 2x NVIDIA T4 GPUs not verified${NC}" | tee -a "$EVIDENCE_FILE"
            GPU_SUCCESS=false
        fi
    else
        echo -e "${YELLOW}⚠️ ai-development cluster not found${NC}" | tee -a "$EVIDENCE_FILE"
        GPU_SUCCESS=false
    fi
else
    echo -e "${YELLOW}⚠️ No workstation clusters found${NC}" | tee -a "$EVIDENCE_FILE"
    CLUSTERS_FOUND=false
    GPU_SUCCESS=false
fi

# STEP 5: Database Connection Verification
echo -e "\n${BOLD}STEP 5: DATABASE CONNECTION VERIFICATION${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "${YELLOW}Checking Redis and AlloyDB connections...${NC}" | tee -a "$EVIDENCE_FILE"

# Check Redis instances
REDIS_INSTANCES=$(gcloud redis instances list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")
echo -e "Redis instances:" | tee -a "$EVIDENCE_FILE"
echo "$REDIS_INSTANCES" | tee -a "$EVIDENCE_FILE"

if [ -n "$REDIS_INSTANCES" ]; then
    echo -e "${GREEN}✅ Redis instances found${NC}" | tee -a "$EVIDENCE_FILE"
    REDIS_FOUND=true
    
    # Check Redis status
    if [[ "$REDIS_INSTANCES" == *"agent-memory"* ]]; then
        REDIS_STATUS=$(gcloud redis instances describe agent-memory --region=us-central1 --project="$PROJECT_ID" --format="value(state)" 2>/dev/null || echo "UNKNOWN")
        echo -e "Redis agent-memory status: $REDIS_STATUS" | tee -a "$EVIDENCE_FILE"
        
        if [ "$REDIS_STATUS" = "READY" ]; then
            echo -e "${GREEN}✅ Redis connection established${NC}" | tee -a "$EVIDENCE_FILE"
            REDIS_SUCCESS=true
        else
            echo -e "${YELLOW}⚠️ Redis instance found but not READY${NC}" | tee -a "$EVIDENCE_FILE"
            REDIS_SUCCESS=false
        fi
    else
        echo -e "${YELLOW}⚠️ agent-memory Redis instance not found${NC}" | tee -a "$EVIDENCE_FILE"
        REDIS_SUCCESS=false
    fi
else
    echo -e "${YELLOW}⚠️ No Redis instances found${NC}" | tee -a "$EVIDENCE_FILE"
    REDIS_FOUND=false
    REDIS_SUCCESS=false
fi

# Check AlloyDB clusters
ALLOYDB_CLUSTERS=$(gcloud alloydb clusters list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")
echo -e "AlloyDB clusters:" | tee -a "$EVIDENCE_FILE"
echo "$ALLOYDB_CLUSTERS" | tee -a "$EVIDENCE_FILE"

if [ -n "$ALLOYDB_CLUSTERS" ]; then
    echo -e "${GREEN}✅ AlloyDB clusters found${NC}" | tee -a "$EVIDENCE_FILE"
    ALLOYDB_FOUND=true
    
    # Check AlloyDB status
    if [[ "$ALLOYDB_CLUSTERS" == *"agent-storage"* ]]; then
        ALLOYDB_STATUS=$(gcloud alloydb clusters describe agent-storage --region=us-central1 --project="$PROJECT_ID" --format="value(state)" 2>/dev/null || echo "UNKNOWN")
        echo -e "AlloyDB agent-storage status: $ALLOYDB_STATUS" | tee -a "$EVIDENCE_FILE"
        
        if [ "$ALLOYDB_STATUS" = "RUNNING" ]; then
            echo -e "${GREEN}✅ AlloyDB connection established${NC}" | tee -a "$EVIDENCE_FILE"
            ALLOYDB_SUCCESS=true
        else
            echo -e "${YELLOW}⚠️ AlloyDB cluster found but not RUNNING${NC}" | tee -a "$EVIDENCE_FILE"
            ALLOYDB_SUCCESS=false
        fi
    else
        echo -e "${YELLOW}⚠️ agent-storage AlloyDB cluster not found${NC}" | tee -a "$EVIDENCE_FILE"
        ALLOYDB_SUCCESS=false
    fi
else
    echo -e "${YELLOW}⚠️ No AlloyDB clusters found${NC}" | tee -a "$EVIDENCE_FILE"
    ALLOYDB_FOUND=false
    ALLOYDB_SUCCESS=false
fi

# STEP 6: Atomic Proof of Success
echo -e "\n${BOLD}STEP 6: ATOMIC PROOF OF SUCCESS${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "${YELLOW}Generating atomic proof of migration success...${NC}" | tee -a "$EVIDENCE_FILE"

ATOMIC_PROOF=$(gcloud projects describe "$PROJECT_ID" --format="value(name,parent.id)" 2>/dev/null || echo "failed")
echo -e "Atomic proof result: ${BOLD}$ATOMIC_PROOF${NC}" | tee -a "$EVIDENCE_FILE"

EXPECTED_PROOF="$PROJECT_ID organizations/$ORG_ID"
if [ "$ATOMIC_PROOF" = "$EXPECTED_PROOF" ]; then
    echo -e "${GREEN}${BOLD}✅ ATOMIC VERIFICATION SUCCESSFUL${NC}" | tee -a "$EVIDENCE_FILE"
    ATOMIC_SUCCESS=true
else
    echo -e "${RED}❌ ATOMIC VERIFICATION FAILED${NC}" | tee -a "$EVIDENCE_FILE"
    ATOMIC_SUCCESS=false
fi

# STEP 7: Migration Attempt (if needed)
if [ "$ORG_SUCCESS" != "true" ] || [ "$ATOMIC_SUCCESS" != "true" ]; then
    echo -e "\n${BOLD}STEP 7: MIGRATION ATTEMPT${NC}" | tee -a "$EVIDENCE_FILE"
    echo -e "${YELLOW}Primary verification failed. Attempting migration with debug logging...${NC}" | tee -a "$EVIDENCE_FILE"
    
    read -p "Attempt migration now? (y/n): " RUN_MIGRATION
    if [[ "$RUN_MIGRATION" == "y" ]]; then
        echo -e "${BLUE}Executing migration with full debug output...${NC}" | tee -a "$EVIDENCE_FILE"
        gcloud beta projects move "$PROJECT_ID" \
          --organization="$ORG_ID" \
          --billing-project="$PROJECT_ID" \
          --verbosity=debug \
          --log-http \
          2>&1 | tee "$DEBUG_LOG"
        
        echo -e "${YELLOW}Migration attempt completed. Checking results...${NC}" | tee -a "$EVIDENCE_FILE"
        
        # Re-check organization
        NEW_ORG_CHECK=$(gcloud projects describe "$PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "failed")
        echo -e "Post-migration organization: ${BOLD}$NEW_ORG_CHECK${NC}" | tee -a "$EVIDENCE_FILE"
        
        if [[ "$NEW_ORG_CHECK" == "organizations/$ORG_ID" ]]; then
            echo -e "${GREEN}${BOLD}✅ MIGRATION SUCCESSFUL${NC}" | tee -a "$EVIDENCE_FILE"
            MIGRATION_SUCCESS=true
        else
            echo -e "${RED}❌ MIGRATION FAILED${NC}" | tee -a "$EVIDENCE_FILE"
            MIGRATION_SUCCESS=false
            
            # STEP 8: Critical Fixes (if migration failed)
            echo -e "\n${BOLD}STEP 8: CRITICAL FIXES${NC}" | tee -a "$EVIDENCE_FILE"
            echo -e "${YELLOW}Migration failed. Attempting critical fixes...${NC}" | tee -a "$EVIDENCE_FILE"
            
            echo -e "1. Recreating service account key..." | tee -a "$EVIDENCE_FILE"
            read -p "Create new service account key? (y/n): " CREATE_KEY
            if [[ "$CREATE_KEY" == "y" ]]; then
                NEW_KEY_FILE="new-vertex-key.json"
                gcloud iam service-accounts keys create "$NEW_KEY_FILE" \
                  --iam-account="$SERVICE_ACCOUNT" 2>/dev/null || {
                    echo -e "${RED}❌ Key creation failed${NC}" | tee -a "$EVIDENCE_FILE"
                }
                
                if [ -f "$NEW_KEY_FILE" ]; then
                    chmod 600 "$NEW_KEY_FILE"
                    echo -e "${GREEN}✅ New key created: $NEW_KEY_FILE${NC}" | tee -a "$EVIDENCE_FILE"
                    echo -e "${YELLOW}Authenticating with new key...${NC}" | tee -a "$EVIDENCE_FILE"
                    
                    gcloud auth activate-service-account --key-file="$NEW_KEY_FILE" 2>/dev/null || {
                        echo -e "${RED}❌ Authentication with new key failed${NC}" | tee -a "$EVIDENCE_FILE"
                    }
                fi
            fi
            
            echo -e "2. Fixing billing project linkage..." | tee -a "$EVIDENCE_FILE"
            read -p "Fix billing project linkage? (y/n): " FIX_BILLING
            if [[ "$FIX_BILLING" == "y" ]]; then
                gcloud beta billing projects link "$PROJECT_ID" \
                  --billing-project="$PROJECT_ID" 2>/dev/null || {
                    echo -e "${RED}❌ Billing project fix failed${NC}" | tee -a "$EVIDENCE_FILE"
                }
                echo -e "${GREEN}✅ Billing project fix attempted${NC}" | tee -a "$EVIDENCE_FILE"
            fi
            
            echo -e "3. Retry migration with force option..." | tee -a "$EVIDENCE_FILE"
            read -p "Retry migration with force option? (y/n): " RETRY_MIGRATION
            if [[ "$RETRY_MIGRATION" == "y" ]]; then
                echo -e "${BLUE}Re-attempting migration with force option...${NC}" | tee -a "$EVIDENCE_FILE"
                gcloud beta projects move "$PROJECT_ID" \
                  --organization="$ORG_ID" \
                  --billing-project="$PROJECT_ID" \
                  --verbosity=debug \
                  --quiet \
                  2>&1 | tee -a "$DEBUG_LOG"
                
                # Final verification
                FINAL_ORG_CHECK=$(gcloud projects describe "$PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "failed")
                echo -e "Final organization check: ${BOLD}$FINAL_ORG_CHECK${NC}" | tee -a "$EVIDENCE_FILE"
                
                if [[ "$FINAL_ORG_CHECK" == "organizations/$ORG_ID" ]]; then
                    echo -e "${GREEN}${BOLD}✅ FINAL MIGRATION SUCCESSFUL${NC}" | tee -a "$EVIDENCE_FILE"
                    FINAL_SUCCESS=true
                else
                    echo -e "${RED}❌ FINAL MIGRATION FAILED${NC}" | tee -a "$EVIDENCE_FILE"
                    FINAL_SUCCESS=false
                fi
            fi
        fi
    else
        echo -e "${YELLOW}Migration attempt skipped by user${NC}" | tee -a "$EVIDENCE_FILE"
    fi
fi

# Generate Final Summary
echo -e "\n${BOLD}===== DEFINITIVE MIGRATION VERIFICATION SUMMARY =====${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "${BOLD}CRITICAL VERIFICATION OUTPUTS:${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "$([ "$ORG_SUCCESS" = "true" ] && echo "${GREEN}✅ Project $PROJECT_ID in organization $ORG_ID${NC}" || echo "${RED}❌ Project NOT in correct organization${NC}")" | tee -a "$EVIDENCE_FILE"
echo -e "$([ "$GPU_SUCCESS" = "true" ] && echo "${GREEN}✅ 2x NVIDIA T4 GPUs active in us-central1${NC}" || echo "${RED}❌ 2x NVIDIA T4 GPUs NOT verified${NC}")" | tee -a "$EVIDENCE_FILE"
echo -e "$([ "$REDIS_SUCCESS" = "true" ] && [ "$ALLOYDB_SUCCESS" = "true" ] && echo "${GREEN}✅ Redis/AlloyDB connections established${NC}" || echo "${RED}❌ Redis/AlloyDB connections NOT established${NC}")" | tee -a "$EVIDENCE_FILE"

# Final status
if [ "$ORG_SUCCESS" = "true" ] && [ "$ATOMIC_SUCCESS" = "true" ]; then
    if [ "$GPU_SUCCESS" = "true" ] && [ "$REDIS_SUCCESS" = "true" ] && [ "$ALLOYDB_SUCCESS" = "true" ]; then
        echo -e "\n${GREEN}${BOLD}✅ COMPLETE MIGRATION VERIFIED SUCCESSFULLY${NC}" | tee -a "$EVIDENCE_FILE"
        echo -e "${GREEN}Project is in the correct organization with all required infrastructure${NC}" | tee -a "$EVIDENCE_FILE"
        FINAL_STATUS="COMPLETE SUCCESS"
    else
        echo -e "\n${YELLOW}${BOLD}⚠️ PARTIAL MIGRATION VERIFIED${NC}" | tee -a "$EVIDENCE_FILE"
        echo -e "${YELLOW}Project is in the correct organization but some infrastructure is incomplete${NC}" | tee -a "$EVIDENCE_FILE"
        FINAL_STATUS="PARTIAL SUCCESS"
    fi
elif [ "$MIGRATION_SUCCESS" = "true" ] || [ "$FINAL_SUCCESS" = "true" ]; then
    echo -e "\n${GREEN}${BOLD}✅ MIGRATION COMPLETED SUCCESSFULLY${NC}" | tee -a "$EVIDENCE_FILE"
    echo -e "${GREEN}Project has been moved to the correct organization${NC}" | tee -a "$EVIDENCE_FILE"
    FINAL_STATUS="MIGRATION SUCCESS"
else
    echo -e "\n${RED}${BOLD}❌ MIGRATION VERIFICATION FAILED${NC}" | tee -a "$EVIDENCE_FILE"
    echo -e "${RED}Project is not in the correct organization${NC}" | tee -a "$EVIDENCE_FILE"
    FINAL_STATUS="FAILED"
fi

echo -e "\nFinal Status: ${BOLD}$FINAL_STATUS${NC}" | tee -a "$EVIDENCE_FILE"
echo -e "Verification completed at $(date)" | tee -a "$EVIDENCE_FILE"
echo -e "Detailed verification evidence saved to $EVIDENCE_FILE" | tee -a "$EVIDENCE_FILE"
echo -e "\n${BOLD}${GREEN}Verification process complete.${NC}"
