#!/bin/bash
# Repository status check
echo "📊 Repository Status Report"
echo "=========================="
gh pr list --repo ai-cherry/orchestra-main
echo ""
echo "Recent commits:"
gh api repos/ai-cherry/orchestra-main/commits --jq '.[0:5] | .[] | "\(.commit.author.date) - \(.commit.message | split("\n")[0])"'
