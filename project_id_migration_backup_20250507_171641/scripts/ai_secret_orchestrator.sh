#!/bin/bash
# Unified secret management with Gemini validation
PROJECT="agi-baby-cherry"
SA="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"

create_secret() {
  SECRET_NAME=$1
  SECRET_VALUE=$2
  
  # Validate with Gemini
  VALIDATION=$(gcloud alpha ai code-assist review \
    --source="$SECRET_VALUE" \
    --category=security \
    --project=$PROJECT \
    --format="value(response)")

  if [[ "$VALIDATION" != "SAFE" ]]; then
    echo "Gemini validation failed for $SECRET_NAME"
    return 1
  fi

  gcloud secrets create $SECRET_NAME \
    --data-file=- \
    --replication-policy=automatic \
    --project=$PROJECT <<< "$SECRET_VALUE"
  
  gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:$SA" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT
}
