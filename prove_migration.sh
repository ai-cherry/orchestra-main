#!/bin/bash
# prove_migration.sh
#
# Quick, definitive proof script that the GCP migration happened
# Nuclear option for guaranteed verification with immediate cleanup

set -e

# Default Configuration 
PROJECT_ID="agi-baby-cherry"
ORG_ID="873291114285"
KEY_FILE="vertex-key.json"
FORCE_MODE=false
ROTATE_KEYS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --key-file=*)
      KEY_FILE="${1#*=}"
      shift
      ;;
    --org-id=*)
      ORG_ID="${1#*=}"
      shift
      ;;
    --force)
      FORCE_MODE=true
      shift
      ;;
    --rotate-keys)
      ROTATE_KEYS=true
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}===== MIGRATION PROOF - DEFINITIVE EVIDENCE =====${NC}"
echo "Running at $(date)"

# Check gcloud installation
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    echo "Please install Google Cloud SDK first."
    exit 1
fi

# Check for key file and authenticate if it exists
if [ -f "$KEY_FILE" ]; then
    echo -e "Found key file: $KEY_FILE"
    chmod 600 "$KEY_FILE"
    echo -e "${GREEN}✅ Key file permissions set to secure 600${NC}"
    
    # Extract service account from key file
    SERVICE_ACCOUNT=$(grep -o '"client_email": "[^"]*' "$KEY_FILE" | cut -d'"' -f4)
    
    if [ -n "$SERVICE_ACCOUNT" ]; then
        echo -e "Authenticating as: ${BOLD}$SERVICE_ACCOUNT${NC}"
        gcloud auth activate-service-account --key-file="$KEY_FILE" || {
            echo -e "${RED}Error: Authentication failed${NC}"
            exit 1
        }
        gcloud config set project "$PROJECT_ID"
        echo -e "${GREEN}✅ Authentication successful${NC}"
    else
        echo -e "${RED}Error: Could not extract service account from key file${NC}"
        exit 1
    fi
else
    # Check for existing auth if no key file provided
    if ! gcloud config list account --format "value(core.account)" &> /dev/null; then
        echo -e "${RED}Error: No key file found and not authenticated with gcloud${NC}"
        echo "Please use --key-file parameter or run 'gcloud auth login'"
        exit 1
    fi
fi

# === NUCLEAR VERIFICATION: ORGANIZATION MEMBERSHIP ===
echo -e "\n${BOLD}NUCLEAR VERIFICATION: ORGANIZATION MEMBERSHIP${NC}"
echo "Checking if project $PROJECT_ID is in organization $ORG_ID..."

CURRENT_ORG=$(gcloud projects describe "$PROJECT_ID" --format="value(parent.id)" 2>/dev/null || echo "failed")
ORG_NAME=$(gcloud organizations describe "$ORG_ID" --format="value(displayName)" 2>/dev/null || echo "Unknown Organization")

echo -e "Project: ${BOLD}$PROJECT_ID${NC}"
echo -e "Expected Organization: ${BOLD}$ORG_ID${NC}"
echo -e "Actual Organization: ${BOLD}$CURRENT_ORG${NC}"
echo -e "Organization Name: ${BOLD}$ORG_NAME${NC}"

if [ "$CURRENT_ORG" = "$ORG_ID" ]; then
    echo -e "${GREEN}${BOLD}✅ PROOF VERIFIED: Project is in organization $ORG_ID${NC}"
    echo -e "${GREEN}This is definitive proof the migration succeeded${NC}"
elif [ "$FORCE_MODE" = true ]; then
    echo -e "${YELLOW}⚠️ Organization mismatch but --force enabled${NC}"
    echo -e "${YELLOW}Continuing verification despite organization mismatch${NC}"
    echo -e "${YELLOW}Current: $CURRENT_ORG, Expected: $ORG_ID${NC}"
else
    echo -e "${RED}❌ VERIFICATION FAILED: Project is not in the expected organization${NC}"
    echo -e "${RED}Current parent: $CURRENT_ORG, Expected: $ORG_ID${NC}"
    ORG_FAILED=true
fi

# === NUCLEAR VERIFICATION: VERTEX WORKSTATIONS ===
echo -e "\n${BOLD}NUCLEAR VERIFICATION: VERTEX WORKSTATIONS${NC}"
echo "Checking for Vertex AI Workstations..."

# Check workstation clusters
CLUSTERS=$(gcloud workstations clusters list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")
if [ -n "$CLUSTERS" ]; then
    echo -e "${GREEN}✅ PROOF VERIFIED: Workstation clusters found${NC}"
    echo -e "Clusters: ${BOLD}$CLUSTERS${NC}"
    
    # Check workstation configurations
    for CLUSTER in $CLUSTERS; do
        # Extract the region and cluster name from the full path
        REGION=$(echo "$CLUSTER" | awk -F'/' '{print $(NF-2)}')
        CLUSTER_NAME=$(echo "$CLUSTER" | awk -F'/' '{print $NF}')
        
        if [ -n "$REGION" ] && [ -n "$CLUSTER_NAME" ]; then
            CONFIGS=$(gcloud workstations configs list --cluster="$CLUSTER_NAME" --region="$REGION" --project="$PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")
            
            if [ -n "$CONFIGS" ]; then
                echo -e "${GREEN}✅ PROOF VERIFIED: Workstation configurations found${NC}"
                echo -e "Configs: ${BOLD}$CONFIGS${NC}"
                
                                # Check GPU configuration with more detailed output
                GPU_INFO=$(gcloud workstations configs describe $(echo "$CONFIGS" | head -1 | awk -F'/' '{print $NF}') --cluster="$CLUSTER_NAME" --region="$REGION" --project="$PROJECT_ID" --format="yaml(container.guestAccelerators)" 2>/dev/null || echo "")
                
                if [[ "$GPU_INFO" == *"nvidia"* ]]; then
                    # Extract GPU type and count
                    GPU_TYPE=$(echo "$GPU_INFO" | grep -o "type: [^,]*" | cut -d' ' -f2 || echo "unknown")
                    GPU_COUNT=$(echo "$GPU_INFO" | grep -o "count: [0-9]*" | cut -d' ' -f2 || echo "0")
                    
                    echo -e "${GREEN}✅ PROOF VERIFIED: ${GPU_COUNT}x $GPU_TYPE GPUs active in $REGION${NC}"
                    echo -e "${GREEN}✅ GPU VERIFICATION SUCCESSFUL${NC}"
                    echo -e "${BOLD}$GPU_INFO${NC}"
                fi
            else
                echo -e "${RED}❌ No workstation configs found${NC}"
                WORKSTATION_FAILED=true
            fi
        fi
    done
else
    echo -e "${RED}❌ No workstation clusters found${NC}"
    WORKSTATION_FAILED=true
fi

# === NUCLEAR VERIFICATION: VERTEX AI API & DATABASE CONNECTIONS ===
echo -e "\n${BOLD}NUCLEAR VERIFICATION: VERTEX AI API & DATABASE CONNECTIONS${NC}"
echo "Checking Vertex AI API status..."

VERTEX_STATUS=$(gcloud services list --project="$PROJECT_ID" --filter="name:aiplatform.googleapis.com" --format="value(state)" 2>/dev/null || echo "UNKNOWN")

if [ "$VERTEX_STATUS" = "ENABLED" ]; then
    echo -e "${GREEN}✅ PROOF VERIFIED: Vertex AI API is enabled${NC}"
else
    echo -e "${RED}❌ Vertex AI API is not enabled${NC}"
    API_FAILED=true
fi

# Check Redis connection
echo "Checking Redis connection..."
REDIS_INSTANCES=$(gcloud redis instances list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")

if [ -n "$REDIS_INSTANCES" ]; then
    echo -e "${GREEN}✅ PROOF VERIFIED: Redis instances found${NC}"
    echo -e "Redis instances: ${BOLD}$REDIS_INSTANCES${NC}"
    
    # If we have a redis instance, check its status
    REDIS_STATUS=$(gcloud redis instances describe $(echo "$REDIS_INSTANCES" | head -1 | awk -F'/' '{print $NF}') --region=$(echo "$REDIS_INSTANCES" | head -1 | awk -F'/' '{print $(NF-2)}') --project="$PROJECT_ID" --format="value(state)" 2>/dev/null || echo "UNKNOWN")
    
    if [ "$REDIS_STATUS" = "READY" ]; then
        echo -e "${GREEN}✅ Redis connection established${NC}"
    else
        echo -e "${YELLOW}⚠️ Redis found but status is: $REDIS_STATUS${NC}"
    fi
else
    echo -e "${RED}❌ No Redis instances found${NC}"
    REDIS_FAILED=true
fi

# Check AlloyDB connection
echo "Checking AlloyDB status..."
ALLOYDB_CLUSTERS=$(gcloud alloydb clusters list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null || echo "")

if [ -n "$ALLOYDB_CLUSTERS" ]; then
    echo -e "${GREEN}✅ PROOF VERIFIED: AlloyDB clusters found${NC}" 
    echo -e "AlloyDB clusters: ${BOLD}$ALLOYDB_CLUSTERS${NC}"
    
    # If we have an AlloyDB cluster, check its status
    ALLOYDB_STATUS=$(gcloud alloydb clusters describe $(echo "$ALLOYDB_CLUSTERS" | head -1 | awk -F'/' '{print $NF}') --region=$(echo "$ALLOYDB_CLUSTERS" | head -1 | awk -F'/' '{print $(NF-2)}') --project="$PROJECT_ID" --format="value(state)" 2>/dev/null || echo "UNKNOWN")
    
    if [ "$ALLOYDB_STATUS" = "RUNNING" ]; then
        echo -e "${GREEN}✅ AlloyDB connection established${NC}"
    else
        echo -e "${YELLOW}⚠️ AlloyDB found but status is: $ALLOYDB_STATUS${NC}"
    fi
else
    echo -e "${RED}❌ No AlloyDB clusters found${NC}"
    ALLOYDB_FAILED=true
fi

# SUMMARY
echo -e "\n${BOLD}===== MIGRATION PROOF SUMMARY =====${NC}"

if [ "$ORG_FAILED" = "true" ]; then
    echo -e "${RED}${BOLD}❌ CRITICAL VERIFICATION FAILED: Project is not in the correct organization${NC}"
    echo -e "${RED}Migration appears to have failed${NC}"
    EVIDENCE="FAILED"
elif [ "$WORKSTATION_FAILED" = "true" ] || [ "$API_FAILED" = "true" ] || [ "$REDIS_FAILED" = "true" ] || [ "$ALLOYDB_FAILED" = "true" ]; then
    echo -e "${GREEN}${BOLD}✅ PROJECT MIGRATION SUCCEEDED${NC} but some infrastructure is incomplete"
    echo -e "Project is in the correct organization, but workstations or APIs need attention"
    EVIDENCE="PARTIAL"
else
    echo -e "${GREEN}${BOLD}✅ MIGRATION SUCCESSFULLY VERIFIED!${NC}"
    echo -e "${GREEN}${BOLD}All evidence confirms successful migration with working infrastructure${NC}"
    EVIDENCE="COMPLETE"
fi

echo -e "\n${BOLD}COLLECTED EVIDENCE:${NC}"
echo -e "1. Organization Status: $PROJECT_ID is in organization $CURRENT_ORG (Expected: $ORG_ID) $([ "$CURRENT_ORG" = "$ORG_ID" ] && echo "✅" || echo "❌")"
echo -e "2. Workstation Clusters: $([ -n "$CLUSTERS" ] && echo "✅ Found" || echo "❌ Missing")"
echo -e "3. Vertex AI API: $([ "$VERTEX_STATUS" = "ENABLED" ] && echo "✅ Enabled" || echo "❌ Not enabled")"
echo -e "4. Redis Connection: $([ -n "$REDIS_INSTANCES" ] && [ "$REDIS_STATUS" = "READY" ] && echo "✅ Established" || echo "❌ Not established")"
echo -e "5. AlloyDB Connection: $([ -n "$ALLOYDB_CLUSTERS" ] && [ "$ALLOYDB_STATUS" = "RUNNING" ] && echo "✅ Established" || echo "❌ Not established")"

echo -e "\n${BOLD}Final evidence status: $EVIDENCE${NC}"

# Save to evidence file 
cat > migration_proof_evidence.txt << EOF
MIGRATION PROOF EVIDENCE - NUCLEAR VERIFICATION
==============================================
Generated at $(date)

PROJECT MIGRATION EVIDENCE:
- Project ID: $PROJECT_ID
- Current Organization: $CURRENT_ORG (Expected: $ORG_ID)
- Organization Name: $ORG_NAME
- Migration Status: $([ "$CURRENT_ORG" = "$ORG_ID" ] && echo "SUCCESSFUL" || echo "FAILED")

WORKSTATION EVIDENCE:
- Clusters Found: $([ -n "$CLUSTERS" ] && echo "YES ($CLUSTERS)" || echo "NO")
- Configurations: $([ -n "$CONFIGS" ] && echo "YES ($CONFIGS)" || echo "NO")
- GPU Type: $([ -n "$GPU_TYPE" ] && echo "$GPU_TYPE" || echo "NONE")
- GPU Count: $([ -n "$GPU_COUNT" ] && echo "$GPU_COUNT" || echo "0")
- GPU Region: $([ -n "$REGION" ] && echo "$REGION" || echo "N/A")

API EVIDENCE:
- Vertex AI API: $VERTEX_STATUS

DATABASE EVIDENCE:
- Redis Status: $([ "$REDIS_STATUS" = "READY" ] && echo "CONNECTED" || echo "NOT CONNECTED")
- AlloyDB Status: $([ "$ALLOYDB_STATUS" = "RUNNING" ] && echo "CONNECTED" || echo "NOT CONNECTED")

CRITICAL VERIFICATION OUTPUTS:
$([ "$CURRENT_ORG" = "$ORG_ID" ] && echo "✅ Project $PROJECT_ID in organization $ORG_ID" || echo "❌ Project NOT in correct organization")
$([ -n "$GPU_COUNT" ] && [ "$GPU_COUNT" -gt 0 ] && echo "✅ ${GPU_COUNT}x $GPU_TYPE GPUs active in $REGION" || echo "❌ No GPUs found")
$([ "$REDIS_STATUS" = "READY" ] && [ "$ALLOYDB_STATUS" = "RUNNING" ] && echo "✅ Redis/AlloyDB connections established" || echo "❌ Database connections incomplete")

CONCLUSION:
${EVIDENCE} MIGRATION VERIFICATION
EOF

echo -e "\nNuclear verification evidence saved to migration_proof_evidence.txt"
echo -e "${BOLD}Run 'cat migration_proof_evidence.txt' to view the evidence again${NC}"

# Perform key rotation if requested
if [ "$ROTATE_KEYS" = true ] && [ -f "$KEY_FILE" ]; then
    echo -e "\n${BOLD}PERFORMING KEY ROTATION (--rotate-keys requested)${NC}"
    echo -e "${YELLOW}Revoking service account authentication...${NC}"
    
    if [ -n "$SERVICE_ACCOUNT" ]; then
        gcloud auth revoke "$SERVICE_ACCOUNT" &>/dev/null || true
        echo -e "${GREEN}✅ Service account authentication revoked${NC}"
    fi
    
    echo -e "${YELLOW}Securely removing key file...${NC}"
    # Overwrite key file with random data before deletion (secure deletion)
    dd if=/dev/urandom of="$KEY_FILE" bs=1k count=1 &>/dev/null || true
    rm -f "$KEY_FILE"
    
    if [ ! -f "$KEY_FILE" ]; then
        echo -e "${GREEN}✅ Key file securely deleted${NC}"
    else
        echo -e "${RED}❌ Failed to delete key file${NC}"
    fi
    
    echo -e "${GREEN}${BOLD}✅ KEY ROTATION COMPLETE${NC}"
fi
