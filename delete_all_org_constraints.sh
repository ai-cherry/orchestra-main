#!/bin/bash
# delete_all_org_constraints.sh
# Remove all org-level org-policy constraints for solo-dev GCP sanity

ORG_ID="145365399613"

echo "Listing all org-level constraints for organization $ORG_ID..."
CONSTRAINTS=$(gcloud org-policies list --organization="$ORG_ID" --format="value(constraint)")

if [[ -z "$CONSTRAINTS" ]]; then
  echo "No org-level constraints found."
  exit 0
fi

echo "Deleting all org-level constraints..."
for CONSTRAINT in $CONSTRAINTS; do
  echo "Deleting $CONSTRAINT ..."
  gcloud org-policies delete "$CONSTRAINT" --organization="$ORG_ID"
done

echo "All org-level org-policy constraints deleted for organization $ORG_ID."
