#!/bin/bash
# Configure API keys for AI coordination System

echo "=== Configuring API Keys ==="

# Function to add a key to the setup command
add_key() {
    local key_name=$1
    local key_value=$2
    if [ -n "$key_value" ]; then
        SETUP_ARGS+=("$key_name=$key_value")
    fi
}

# Initialize setup arguments array
SETUP_ARGS=()

# AI Service API Keys (already configured)
add_key "ANTHROPIC_API_KEY" "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"
add_key "FIGMA_PERSONAL_ACCESS_TOKEN" "figd_PMCxgzYY_zln_7pJKkHSkaf-lyzyKMemjMDDt_LJ"
add_key "ELEVEN_LABS_API_KEY" "sk_0b68a8ac28119888145589965bf097211889379a3da2ad41"
add_key "GROK_AI_API_KEY" "xai-CzmpqJkNgmZD50RXirelj06Lyljk3d6y530IczCJNcDoiAHefnov5pFdHPBi0GoFFxncrz8ulMZtPeUk"
add_key "MISTRAL_API_KEY" "jCGVZEeBzppPH0pPVL0vxRCPnZuWL90i"
add_key "NOTION_API_KEY" "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"
add_key "OPENAI_API_KEY" "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"
add_key "OPENROUTER_API_KEY" "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"
add_key "PERPLEXITY_API_KEY" "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"
add_key "PHANTOM_BUSTER_API_KEY" "C7CC5X14znGscbe9C7uUOOeHeFAAvpA8N8SbOUo18m4"
add_key "PORTKEY_API_KEY" "hPxFZGd8AN269n4bznDf2/Onbi8I"
add_key "PORTKEY_CONFIG" "pc-portke-b43e56"

# Infrastructure keys
add_key "LAMBDA_API_KEY" "7L34HOKF25HYDT7WHETR7QZTHQX6M5YP36MQ"

# Airbyte configuration
add_key "AIRBYTE_CLIENT_ID" "9630134c-359d-4c9c-aa97-95ab3a2ff8f5"
add_key "AIRBYTE_CLIENT_SECRET" "NfwyhFUjemKlC66h7iECE9Tjedo6SGFh"
add_key "AIRBYTE_ACCESS_TOKEN" "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6Z1BPdmhDSC1Ic21OQnhhV3lnLU11dlF6dHJERTBDSEJHZDB2MVh0Vnk0In0.eyJleHAiOjE3NDg5MjQyMTIsImlhdCI6MTc0ODkyMzMxMiwianRpIjoiYzYwYzFiZmYtMTBkMC00N2E0LWEyYzEtMmRiYWEyNDk2YzkwIiwiaXNzIjoiaHR0cHM6Ly9jbG91ZC5haXJieXRlLmNvbS9hdXRoL3JlYWxtcy9fYWlyYnl0ZS1hcHBsaWNhdGlvbi1jbGllbnRzIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjkwNzJmYzI0LTE0MjUtNDBlNy05ZmU4LTg0ZWYxM2I2M2Q4MCIsInR5cCI6IkJlYXJlciIsImF6cCI6Ijk2MzAxMzRjLTM1OWQtNGM5Yy1hYTk3LTk1YWIzYTJmZjhmNSIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtX2FpcmJ5dGUtYXBwbGljYXRpb24tY2xpZW50cyJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImNsaWVudEhvc3QiOiIxNzIuMjMuMy4yMjYiLCJ1c2VyX2lkIjoiOTA3MmZjMjQtMTQyNS00MGU3LTlmZTgtODRlZjEzYjYzZDgwIiwicHJlZmVycmVkX3VzZXJuYW1lIjoic2VydmljZS1hY2NvdW50LTk2MzAxMzRjLTM1OWQtNGM5Yy1hYTk3LTk1YWIzYTJmZjhmNSIsImNsaWVudEFkZHJlc3MiOiIxNzIuMjMuMy4yMjYiLCJjbGllbnRfaWQiOiI5NjMwMTM0Yy0zNTlkLTRjOWMtYWE5Ny05NWFiM2EyZmY4ZjUifQ.ajeY7s3lzyI6OGDlA6k08r0cRIRMMqiH-646ozDpBVBc8941tjldavLA4lFgo4fxa4DuXFvcD0-lq2xN-yfkzaKWm7fz9rRu7Op2Y4YgoFs3MFvSprQOUqAHLnUI3OeHGSwSq2DBtA7dMuKY4XBGbfs96_U_1fFXglhYslQevcYUu3Rs12-OADUMVipioSHNEqRqEqrbjc2gsguT-6Xj9oghA-IJ0cFe232xkhCfWWDuC8fV-41GF8kCN7xL3L14RoKyvXgVV7qjuURw2OKWydClunMyEeCn1mlfpw2gWLjXPVjgli0kHPqH0-K095g0GjVfaIBFLxumza1GQiqaPg"

# No AWS - using local Pulumi state as requested

# Run the setup script with all API keys
python3 scripts/setup_api_keys.py "${SETUP_ARGS[@]}"

echo
echo "=== API Keys Configuration Complete ==="
echo
echo "✅ All keys are saved in .env file - you NEVER need to enter them again!"
echo "✅ They're automatically loaded every time you run the conductor!"
echo
echo "To add infrastructure keys later, just edit this script and uncomment the lines."