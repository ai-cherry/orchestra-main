#!/bin/bash
# Clean git history of exposed secrets
set -euo pipefail

echo "🧹 Cleaning git history of exposed secrets..."
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "   Make sure you have a backup of your repository."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Create a backup branch
echo "📦 Creating backup branch..."
git branch backup-before-secret-cleanup 2>/dev/null || true

# Remove the problematic commit that contains secrets
echo "🔧 Removing commit e18ece0 that contains exposed secrets..."

# Use git filter-branch to remove the specific commit
git filter-branch --force --index-filter \
  'if [ "$GIT_COMMIT" = "e18ece061528fa1e6613353ff375943c403d2eab" ]; then
     git rm --cached -r . 2>/dev/null || true
   fi' \
  --prune-empty --tag-name-filter cat -- --all

# Alternative: Remove specific files from history
echo "🔧 Removing .env and setup_all_secrets.sh from history..."
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env scripts/setup_all_secrets.sh' \
  --prune-empty --tag-name-filter cat -- --all

# Clean up
echo "🧹 Cleaning up..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✅ Git history cleaned!"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. Review the changes: git log --oneline"
echo "2. Force push to remote: git push --force origin main"
echo "3. Notify all team members to re-clone the repository"
echo "4. Rotate all exposed API keys:"
echo "   - OpenAI API key"
echo "   - Anthropic API key"
echo "   - DigitalOcean token"
echo ""
echo "5. Update the new keys in Pulumi:"
echo "   cd infra"
echo "   pulumi config set --secret openai_api_key <new-key>"
echo "   pulumi config set --secret anthropic_api_key <new-key>"
echo "   pulumi config set --secret digitalocean:token <new-token>"
echo ""
echo "6. Regenerate .env:"
echo "   python scripts/generate_env_from_pulumi.py"
