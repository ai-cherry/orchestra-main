#!/bin/bash
# use_claude_code_examples.sh
#
# Examples of how to use Claude Code with GCP project migration
# These commands demonstrate how Claude Code can assist with various migration tasks
# Must be run after installing Claude Code with setup_claude_code.sh

set -e

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== Claude Code GCP Migration Examples =====${NC}"

# -----[ Display Examples ]-----
echo -e "\n${YELLOW}Pre-Migration Analysis${NC}"
echo -e "${BLUE}Run these commands to analyze your project before migration:${NC}"
echo -e "${GREEN}cd /workspaces/orchestra-main${NC}"
echo -e "${GREEN}claude \"analyze if project agi-baby-cherry is ready for migration to organization 873291114285\"${NC}"
echo -e "${GREEN}claude \"identify potential blockers for GCP project migration\"${NC}"
echo -e "${GREEN}claude \"check if service account vertex-agent@agi-baby-cherry.iam.gserviceaccount.com has sufficient permissions\"${NC}"

echo -e "\n${YELLOW}Migration Planning${NC}"
echo -e "${BLUE}Run these commands to get migration planning assistance:${NC}"
echo -e "${GREEN}claude \"create a detailed migration plan for moving agi-baby-cherry to organization 873291114285\"${NC}"
echo -e "${GREEN}claude \"generate a migration checklist with verification steps\"${NC}"
echo -e "${GREEN}claude \"suggest rollback procedures in case migration fails\"${NC}"

echo -e "\n${YELLOW}IAM Troubleshooting${NC}"
echo -e "${BLUE}Run these commands if you encounter IAM issues:${NC}"
echo -e "${GREEN}claude \"diagnose why I'm getting PERMISSION_DENIED during project move\"${NC}"
echo -e "${GREEN}claude \"explain IAM propagation delays and how to handle them\"${NC}"
echo -e "${GREEN}claude \"generate commands to verify and fix IAM bindings\"${NC}"

echo -e "\n${YELLOW}Terraform Optimization${NC}"
echo -e "${BLUE}Run these commands to optimize your Terraform configuration:${NC}"
echo -e "${GREEN}claude \"analyze and optimize our hybrid_workstation_config.tf\"${NC}"
echo -e "${GREEN}claude \"suggest best practices for our cloud workstation configuration\"${NC}"
echo -e "${GREEN}claude \"recommend security improvements for our Terraform config\"${NC}"

echo -e "\n${YELLOW}Post-Migration Verification${NC}"
echo -e "${BLUE}Run these commands to verify migration success:${NC}"
echo -e "${GREEN}claude \"create comprehensive verification script for our GCP migration\"${NC}"
echo -e "${GREEN}claude \"generate commands to check all migrated resources\"${NC}"
echo -e "${GREEN}claude \"create a post-migration report template\"${NC}"

echo -e "\n${YELLOW}Extended Thinking Demonstrations${NC}"
echo -e "${BLUE}These commands demonstrate Claude's extended thinking capabilities:${NC}"
echo -e "${GREEN}claude \"think deeply about optimizing our hybrid IDE for Vertex AI performance\"${NC}"
echo -e "${GREEN}claude \"think hard about potential security risks in our cloud workstation setup\"${NC}"
echo -e "${GREEN}claude \"think about cost optimization strategies for our GCP setup\"${NC}"

echo -e "\n${YELLOW}Automation Examples${NC}"
echo -e "${BLUE}Run these commands to generate automation scripts:${NC}"
echo -e "${GREEN}claude \"create a daily health check script for our GCP environment\"${NC}"
echo -e "${GREEN}claude \"generate a backup and recovery script for our cloud workstation\"${NC}"
echo -e "${GREEN}claude \"create a dashboard monitoring script for our hybrid IDE\"${NC}"

echo -e "\n${YELLOW}Using Claude Code in Non-Interactive Mode${NC}"
echo -e "${BLUE}Examples of using Claude Code in scripts:${NC}"
echo -e "${GREEN}claude -p \"verify our GCP migration\" --allowedTools \"Bash(gcloud:*)\" > migration_verification_results.txt${NC}"
echo -e "${GREEN}claude -p \"optimize our Terraform\" --allowedTools \"Read\" \"Write\" > terraform_optimization.md${NC}"
echo -e "${GREEN}claude -p \"generate monitoring script\" --json | jq '.response.content' > monitoring.sh${NC}"

echo -e "\n${GREEN}===== End of Claude Code Examples =====${NC}"
echo -e "${BLUE}Note: Claude Code operates directly in your terminal, tapping into Claude's intelligence while maintaining project context awareness.${NC}"
echo -e "${BLUE}Use these examples as starting points and adapt them to your specific needs.${NC}"
