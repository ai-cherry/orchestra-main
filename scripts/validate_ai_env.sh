#!/bin/bash
# Validate AI environment setup
check_gcp_auth() {
  gcloud auth list --filter=status:ACTIVE | grep "vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"
}

test_gemini() {
  gcloud alpha ai code-assist review \
    --source=core/llm_orchestrator.py \
    --project=agi-baby-cherry \
    --category=security
}

check_vertex_model() {
  gcloud ai models list --project=agi-baby-cherry | grep "gemini-pro"
}

check_gcp_auth && test_gemini && check_vertex_model
