#!/bin/bash
# Lint check: ban raw Terraform backends if using Terragrunt
if grep -R --include='*.tf' -qe 'backend "' terraform/; then
  echo "Use Terragrunt for back-ends, not local tf files"; exit 1; fi
