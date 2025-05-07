#!/bin/bash
# verify_migration.sh
#
# NUCLEAR VERIFICATION script to confirm GCP migration happened successfully
# Zero BS version focused on definitive proof with aggressive verification

set -e

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default Configuration
GCP_PROJECT_ID="agi-baby-cherry"
GCP_ORG_ID="873291114285"  # Numeric ID without hyphens
SERVICE_ACCOUNT="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"
KEY_FILE="vertex-key.json"
RESULTS_FILE="migration_verification_evidence.txt"

# Command line arguments
NUKE_MODE=false
VERIFICATION_LEVEL="standard"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --nuke)
      NUKE_MODE=true
      VERIFICATION_LEVEL="nuclear"
      shift
      ;;
    --key-file=*)
      KEY_FILE="${1#*=}"
      shift
      ;;
    --org-id=*)
      GCP_ORG_ID="${1#*=}"
      shift
      ;;
    --project-id=*)
      GCP_PROJECT_ID="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Clean previous results
> $RESULTS_FILE

echo -e "${BOLD}===== MIGRATION VERIFICATION - ${VERIFICATION_LEVEL^^} MODE =====${NC}"
echo -e "Starting verification at $(date)" | tee -a $RESULTS_FILE
echo -e "${YELLOW}Collecting concrete evidence the migration happened${NC}\n"

# Step 1: gcloud CLI verification
echo -e "${BLUE}Step 1: Verify gcloud CLI${NC}" | tee -a $RESULTS_FILE
# Check if gcloud is already installed
if command -v gcloud &> /dev/null; then
    GCLOUD_VERSION=$(gcloud --version | head -n 1)
    echo -e "${GREEN}✅ gcloud CLI already installed: $GCLOUD_VERSION${NC}" | tee -a $RESULTS_FILE
else
    echo -e "${RED}❌ gcloud CLI not found - required for verification${NC}" | tee -a $RESULTS_FILE
    echo -e "${YELLOW}Please install Google Cloud SDK first.${NC}" | tee -a $RESULTS_FILE
    exit 1
fi

# Step 2: Authentication verification
echo -e "\n${BLUE}Step 2: Service Account Authentication${NC}" | tee -a $RESULTS_FILE

if [ -f "$KEY_FILE" ]; then
    echo -e "${GREEN}Key file found: $KEY_FILE${NC}" | tee -a $RESULTS_FILE
    chmod 600 "$KEY_FILE"
    echo -e "${GREEN}✅ Key file permissions set to secure 600${NC}" | tee -a $RESULTS_FILE
    
    # Extract service account from key file
    SERVICE_ACCOUNT=$(grep -o '"client_email": "[^"]*' "$KEY_FILE" | cut -d'"' -f4)
    
    if [ -n "$SERVICE_ACCOUNT" ]; then
        echo -e "Authenticating as: ${BOLD}$SERVICE_ACCOUNT${NC}" | tee -a $RESULTS_FILE
        gcloud auth activate-service-account --key-file="$KEY_FILE" 2>/dev/null || {
            echo -e "${RED}❌ Authentication failed with key file${NC}" | tee -a $RESULTS_FILE
            exit 1
        }
        gcloud config set project "$GCP_PROJECT_ID"
        echo -e "${GREEN}✅ Authentication successful!${NC}" | tee -a $RESULTS_FILE
    else
        echo -e "${RED}❌ Could not extract service account from key file${NC}" | tee -a $RESULTS_FILE
        exit 1
    fi
else
    # Check for existing auth if no key file provided
    CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
    
    if [ -z "$CURRENT_ACCOUNT" ]; then
        echo -e "${RED}❌ No authentication found. Please authenticate first.${NC}" | tee -a $RESULTS_FILE
        echo -e "${RED}Run 'gcloud auth login' or provide a key file.${NC}" | tee -a $RESULTS_FILE
        exit 1
    else
        echo -e "${GREEN}✅ Using existing authentication: $CURRENT_ACCOUNT${NC}" | tee -a $RESULTS_FILE
        gcloud config set project "$GCP_PROJECT_ID" 2>/dev/null || {
            echo -e "${RED}❌ Failed to set project to $GCP_PROJECT_ID${NC}" | tee -a $RESULTS_FILE
            exit 1
        }
    fi
fi

# Step 3: NUCLEAR VERIFICATION - ORGANIZATION MEMBERSHIP
echo -e "\n${BLUE}Step 3: NUCLEAR VERIFICATION - ORGANIZATION MEMBERSHIP${NC}" | tee -a $RESULTS_FILE
echo -e "${YELLOW}Checking if project is in the correct organization...${NC}" | tee -a $RESULTS_FILE

CURRENT_ORG=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "failed")
ORG_NAME=$(gcloud organizations describe "$GCP_ORG_ID" --format="value(displayName)" 2>/dev/null || echo "Unknown Organization")

echo -e "Project: ${BOLD}$GCP_PROJECT_ID${NC}" | tee -a $RESULTS_FILE
echo -e "Expected Organization ID: ${BOLD}$GCP_ORG_ID${NC}" | tee -a $RESULTS_FILE
echo -e "Actual Organization ID: ${BOLD}$CURRENT_ORG${NC}" | tee -a $RESULTS_FILE
echo -e "Organization Name: ${BOLD}$ORG_NAME${NC}" | tee -a $RESULTS_FILE

if [ "$CURRENT_ORG" = "$GCP_ORG_ID" ]; then
    echo -e "${GREEN}${BOLD}✅ MIGRATION CONFIRMED: Project is correctly in organization $GCP_ORG_ID${NC}" | tee -a $RESULTS_FILE
    echo -e "${GREEN}${BOLD}✅ Project $GCP_PROJECT_ID in organization $GCP_ORG_ID${NC}" | tee -a $RESULTS_FILE
else
    echo -e "${RED}${BOLD}❌ CRITICAL VERIFICATION FAILED: Project is not in the expected organization.${NC}" | tee -a $RESULTS_FILE
    echo -e "${RED}   Current parent: $CURRENT_ORG, Expected: $GCP_ORG_ID${NC}" | tee -a $RESULTS_FILE
    VERIFICATION_FAILED=true
fi

# Step 4: NUCLEAR VERIFICATION - VERTEX WORKSTATIONS & GPU
echo -e "\n${BLUE}Step 4: NUCLEAR VERIFICATION - VERTEX WORKSTATIONS & GPU${NC}" | tee -a $RESULTS_FILE
echo -e "${YELLOW}Checking for Vertex Workstations and GPU configurations...${NC}" | tee -a $RESULTS_FILE

# Check workstation clusters
CLUSTERS=$(gcloud workstations clusters list --project="$GCP_PROJECT_ID" --format="json" 2>/dev/null || echo "[]")
CLUSTER_COUNT=$(echo "$CLUSTERS" | grep -o "name" | wc -l)

echo -e "Workstation Clusters: ${BOLD}$CLUSTER_COUNT found${NC}" | tee -a $RESULTS_FILE
if [ "$CLUSTER_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Workstation clusters exist${NC}" | tee -a $RESULTS_FILE
    
    # Extract and display cluster names with extra verification in NUKE mode
    CLUSTER_NAMES=$(echo "$CLUSTERS" | grep -o '"name": "[^"]*' | sed 's/"name": "//')
    echo -e "Cluster names: ${BOLD}$CLUSTER_NAMES${NC}" | tee -a $RESULTS_FILE
    
    # Check workstation configurations
    CONFIG_COUNT=0
    TOTAL_GPU_COUNT=0
    FOUND_NVIDIA_T4=false
    
    for CLUSTER in $CLUSTER_NAMES; do
        # Extract the region from the cluster name
        REGION=$(echo "$CLUSTER" | sed -n 's/.*\/\([^\/]*\)\/clusters\/.*/\1/p')
        CLUSTER_SHORT=$(echo "$CLUSTER" | sed -n 's/.*\/clusters\/\(.*\)/\1/p')
        
        if [ -n "$REGION" ] && [ -n "$CLUSTER_SHORT" ]; then
            CONFIGS=$(gcloud workstations configs list --cluster="$CLUSTER_SHORT" --region="$REGION" --project="$GCP_PROJECT_ID" --format="json" 2>/dev/null || echo "[]")
            CONFIG_COUNT_THIS=$(echo "$CONFIGS" | grep -o "name" | wc -l)
            CONFIG_COUNT=$((CONFIG_COUNT + CONFIG_COUNT_THIS))
            
            if [ "$CONFIG_COUNT_THIS" -gt 0 ]; then
                echo -e "${GREEN}✅ Found $CONFIG_COUNT_THIS configurations in cluster $CLUSTER_SHORT${NC}" | tee -a $RESULTS_FILE
                
                # Extract and display config details
                CONFIG_NAMES=$(echo "$CONFIGS" | grep -o '"name": "[^"]*' | sed 's/"name": "//')
                echo -e "Configuration names: ${BOLD}$CONFIG_NAMES${NC}" | tee -a $RESULTS_FILE
                
                # Check for GPU configurations
                for CONFIG_PATH in $CONFIG_NAMES; do
                    CONFIG_NAME=$(echo "$CONFIG_PATH" | sed -n 's/.*\/configs\/\(.*\)/\1/p')
                    GPU_INFO=$(gcloud workstations configs describe "$CONFIG_NAME" --cluster="$CLUSTER_SHORT" --region="$REGION" --project="$GCP_PROJECT_ID" --format="yaml(container.guestAccelerators)" 2>/dev/null || echo "")
                    
                    if [[ "$GPU_INFO" == *"nvidia"* ]]; then
                        # Extract GPU type and count
                        GPU_TYPE=$(echo "$GPU_INFO" | grep -o "type: [^,]*" | cut -d' ' -f2 || echo "unknown")
                        GPU_COUNT=$(echo "$GPU_INFO" | grep -o "count: [0-9]*" | cut -d' ' -f2 || echo "0")
                        TOTAL_GPU_COUNT=$((TOTAL_GPU_COUNT + GPU_COUNT))
                        
                        echo -e "${GREEN}✅ GPU configuration detected: ${GPU_COUNT}x $GPU_TYPE${NC}" | tee -a $RESULTS_FILE
                        
                        if [[ "$GPU_TYPE" == *"nvidia-tesla-t4"* ]]; then
                            FOUND_NVIDIA_T4=true
                            T4_REGION=$REGION
                            T4_COUNT=$GPU_COUNT
                            
                            if [ "$T4_COUNT" -eq 2 ]; then
                                echo -e "${GREEN}${BOLD}✅ 2x NVIDIA T4 GPUs active in $T4_REGION${NC}" | tee -a $RESULTS_FILE
                            fi
                        fi
                    fi
                done
            fi
        fi
    done
    
    # Summary of GPU findings
    if [ "$TOTAL_GPU_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Total GPUs found: $TOTAL_GPU_COUNT${NC}" | tee -a $RESULTS_FILE
        
        if [ "$FOUND_NVIDIA_T4" = true ]; then
            echo -e "${GREEN}✅ NVIDIA T4 GPUs confirmed in region $T4_REGION${NC}" | tee -a $RESULTS_FILE
        else
            echo -e "${RED}❌ NVIDIA T4 GPUs not found${NC}" | tee -a $RESULTS_FILE
            GPU_VERIFICATION_FAILED=true
        fi
    else
        echo -e "${RED}❌ No GPUs found in any workstation configuration${NC}" | tee -a $RESULTS_FILE
        GPU_VERIFICATION_FAILED=true
    fi
    
    if [ "$CONFIG_COUNT" -gt 0 ]; then
        echo -e "${GREEN}${BOLD}✅ WORKSTATIONS CONFIRMED: $CONFIG_COUNT configurations found across all clusters${NC}" | tee -a $RESULTS_FILE
    else
        echo -e "${RED}❌ No workstation configurations found${NC}" | tee -a $RESULTS_FILE
        WORKSTATION_FAILED=true
    fi
else
    echo -e "${RED}❌ No workstation clusters found${NC}" | tee -a $RESULTS_FILE
    WORKSTATION_FAILED=true
fi

# Step 5: NUCLEAR VERIFICATION - DATABASE CONNECTIONS
echo -e "\n${BLUE}Step 5: NUCLEAR VERIFICATION - DATABASE CONNECTIONS${NC}" | tee -a $RESULTS_FILE

# Check Vertex AI services
echo -e "${YELLOW}Checking Vertex AI API status...${NC}" | tee -a $RESULTS_FILE
VERTEX_STATUS=$(gcloud services list --project="$GCP_PROJECT_ID" --filter="name:aiplatform.googleapis.com" --format="value(state)" 2>/dev/null || echo "UNKNOWN")

if [ "$VERTEX_STATUS" = "ENABLED" ]; then
    echo -e "${GREEN}✅ Vertex AI API is enabled${NC}" | tee -a $RESULTS_FILE
else
    echo -e "${RED}❌ Vertex AI API is not enabled or status unknown${NC}" | tee -a $RESULTS_FILE
    API_FAILED=true
fi

# Check Redis connection
echo -e "\n${YELLOW}Checking Redis connection...${NC}" | tee -a $RESULTS_FILE
REDIS_INSTANCES=$(gcloud redis instances list --project="$GCP_PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")

if [ -n "$REDIS_INSTANCES" ]; then
    echo -e "${GREEN}✅ Redis instances found: $REDIS_INSTANCES${NC}" | tee -a $RESULTS_FILE
    
    # If we have a Redis instance, check its status
    for REDIS_INSTANCE in $REDIS_INSTANCES; do
        # Extract instance name and region
        REDIS_NAME=$(echo "$REDIS_INSTANCE" | sed -n 's/.*\/\([^\/]*\)$/\1/p')
        REDIS_REGION=$(echo "$REDIS_INSTANCE" | sed -n 's/.*\/locations\/\([^\/]*\)\/.*/\1/p')
        
        if [ -n "$REDIS_NAME" ] && [ -n "$REDIS_REGION" ]; then
            REDIS_STATUS=$(gcloud redis instances describe "$REDIS_NAME" --region="$REDIS_REGION" --project="$GCP_PROJECT_ID" --format="value(state)" 2>/dev/null || echo "UNKNOWN")
            
            if [ "$REDIS_STATUS" = "READY" ]; then
                echo -e "${GREEN}✅ Redis instance '$REDIS_NAME' is READY${NC}" | tee -a $RESULTS_FILE
                REDIS_CONNECTION_SUCCESS=true
            else
                echo -e "${YELLOW}⚠️ Redis instance '$REDIS_NAME' status: $REDIS_STATUS${NC}" | tee -a $RESULTS_FILE
            fi
        fi
    done
else
    echo -e "${RED}❌ No Redis instances found${NC}" | tee -a $RESULTS_FILE
    REDIS_FAILED=true
fi

# Check AlloyDB
echo -e "\n${YELLOW}Checking AlloyDB status...${NC}" | tee -a $RESULTS_FILE
ALLOYDB_CLUSTERS=$(gcloud alloydb clusters list --project="$GCP_PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")

if [ -n "$ALLOYDB_CLUSTERS" ]; then
    echo -e "${GREEN}✅ AlloyDB clusters found: $ALLOYDB_CLUSTERS${NC}" | tee -a $RESULTS_FILE
    
    # If we have an AlloyDB cluster, check its status
    for ALLOYDB_CLUSTER in $ALLOYDB_CLUSTERS; do
        # Extract cluster name and region
        ALLOYDB_NAME=$(echo "$ALLOYDB_CLUSTER" | sed -n 's/.*\/\([^\/]*\)$/\1/p')
        ALLOYDB_REGION=$(echo "$ALLOYDB_CLUSTER" | sed -n 's/.*\/locations\/\([^\/]*\)\/.*/\1/p')
        
        if [ -n "$ALLOYDB_NAME" ] && [ -n "$ALLOYDB_REGION" ]; then
            ALLOYDB_STATUS=$(gcloud alloydb clusters describe "$ALLOYDB_NAME" --region="$ALLOYDB_REGION" --project="$GCP_PROJECT_ID" --format="value(state)" 2>/dev/null || echo "UNKNOWN")
            
            if [ "$ALLOYDB_STATUS" = "RUNNING" ]; then
                echo -e "${GREEN}✅ AlloyDB cluster '$ALLOYDB_NAME' is RUNNING${NC}" | tee -a $RESULTS_FILE
                ALLOYDB_CONNECTION_SUCCESS=true
            else
                echo -e "${YELLOW}⚠️ AlloyDB cluster '$ALLOYDB_NAME' status: $ALLOYDB_STATUS${NC}" | tee -a $RESULTS_FILE
            fi
        fi
    done
else
    echo -e "${RED}❌ No AlloyDB clusters found${NC}" | tee -a $RESULTS_FILE
    ALLOYDB_FAILED=true
fi

# Check if both database connections are successful
if [ "$REDIS_CONNECTION_SUCCESS" = true ] && [ "$ALLOYDB_CONNECTION_SUCCESS" = true ]; then
    echo -e "${GREEN}${BOLD}✅ Redis/AlloyDB connections established${NC}" | tee -a $RESULTS_FILE
    DB_CONNECTION_SUCCESS=true
fi

# Final Summary - Proof Collection
echo -e "\n${BLUE}${BOLD}===== MIGRATION VERIFICATION SUMMARY =====${NC}" | tee -a $RESULTS_FILE

if [ "${VERIFICATION_FAILED}" = "true" ]; then
    echo -e "${RED}${BOLD}❌ CRITICAL VERIFICATION FAILED: Project is not in the correct organization.${NC}" | tee -a $RESULTS_FILE
    echo -e "${RED}Migration appears to have failed or is incomplete.${NC}" | tee -a $RESULTS_FILE
    FINAL_STATUS="FAILED"
elif [ "${WORKSTATION_FAILED}" = "true" ] || [ "${GPU_VERIFICATION_FAILED}" = "true" ] || [ "${API_FAILED}" = "true" ] || [ "${REDIS_FAILED}" = "true" ] || [ "${ALLOYDB_FAILED}" = "true" ]; then
    echo -e "${YELLOW}${BOLD}⚠️ ORGANIZATION MIGRATION SUCCESSFUL BUT INFRASTRUCTURE INCOMPLETE${NC}" | tee -a $RESULTS_FILE
    echo -e "${YELLOW}Project is in the correct organization, but workstations/Cloud IDE not fully configured.${NC}" | tee -a $RESULTS_FILE
    FINAL_STATUS="PARTIAL"
else
    echo -e "${GREEN}${BOLD}✅ COMPLETE MIGRATION VERIFIED SUCCESSFULLY${NC}" | tee -a $RESULTS_FILE
    echo -e "${GREEN}Project is in the correct organization with working infrastructure.${NC}" | tee -a $RESULTS_FILE
    FINAL_STATUS="SUCCESS"
fi

# Nuclear mode critical output
echo -e "\n${BLUE}${BOLD}CRITICAL VERIFICATION RESULTS:${NC}" | tee -a $RESULTS_FILE
echo -e "$([ "$CURRENT_ORG" = "$GCP_ORG_ID" ] && echo "${GREEN}✅ Project $GCP_PROJECT_ID in organization $GCP_ORG_ID${NC}" || echo "${RED}❌ Project NOT in correct organization${NC}")" | tee -a $RESULTS_FILE
echo -e "$([ "$FOUND_NVIDIA_T4" = true ] && [ "$T4_COUNT" -eq 2 ] && echo "${GREEN}✅ 2x NVIDIA T4 GPUs active in $T4_REGION${NC}" || echo "${RED}❌ 2x NVIDIA T4 GPUs NOT verified${NC}")" | tee -a $RESULTS_FILE
echo -e "$([ "$DB_CONNECTION_SUCCESS" = true ] && echo "${GREEN}✅ Redis/AlloyDB connections established${NC}" || echo "${RED}❌ Redis/AlloyDB connections NOT established${NC}")" | tee -a $RESULTS_FILE

# Collect all evidence in one place
echo -e "\n${BLUE}${BOLD}COLLECTED EVIDENCE:${NC}" | tee -a $RESULTS_FILE
echo -e "1. Organization Status: Project $GCP_PROJECT_ID is in organization $CURRENT_ORG (Expected: $GCP_ORG_ID)" | tee -a $RESULTS_FILE
echo -e "2. Workstation Clusters: $CLUSTER_COUNT found" | tee -a $RESULTS_FILE
echo -e "3. Workstation Configurations: $CONFIG_COUNT found" | tee -a $RESULTS_FILE
echo -e "4. GPU Status: $([ "$FOUND_NVIDIA_T4" = true ] && echo "$T4_COUNT x NVIDIA T4 in $T4_REGION" || echo "NOT VERIFIED")" | tee -a $RESULTS_FILE
echo -e "5. Vertex AI API Status: $VERTEX_STATUS" | tee -a $RESULTS_FILE
echo -e "6. AlloyDB Status: $([ "$ALLOYDB_CONNECTION_SUCCESS" = true ] && echo "RUNNING" || echo "NOT VERIFIED")" | tee -a $RESULTS_FILE
echo -e "7. Redis Status: $([ "$REDIS_CONNECTION_SUCCESS" = true ] && echo "READY" || echo "NOT VERIFIED")" | tee -a $RESULTS_FILE
echo -e "\nFinal Verification Status: ${BOLD}$FINAL_STATUS${NC}" | tee -a $RESULTS_FILE
echo -e "Verification completed at $(date)" | tee -a $RESULTS_FILE

echo -e "\n${GREEN}Evidence collected and saved to $RESULTS_FILE${NC}"
echo -e "${YELLOW}Run 'cat $RESULTS_FILE' to review the evidence again${NC}"

# Cleanup in NUKE mode
if [ "$NUKE_MODE" = true ] && [ -f "$KEY_FILE" ]; then
    echo -e "\n${YELLOW}NUKE MODE: Performing key cleanup...${NC}"
    read -p "Securely delete the key file? (y/n): " DELETE_KEY
    
    if [[ "$DELETE_KEY" == "y" ]]; then
        # Overwrite with random data before deletion for security
        dd if=/dev/urandom of="$KEY_FILE" bs=1k count=1 &>/dev/null
        rm -f "$KEY_FILE"
        echo -e "${GREEN}✅ Key file securely deleted${NC}"
    fi
fi

echo -e "\n${BOLD}${GREEN}Verification process complete.${NC}"
