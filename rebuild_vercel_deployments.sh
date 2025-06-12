#!/bin/bash
# Vercel Rebuild Script - Generated on 2025-06-12 16:08:35
# This script will rebuild Vercel deployments to match the current codebase

set -e

echo "🚀 Starting Vercel Rebuild Process"
echo "================================="

# Export Vercel token
export VERCEL_TOKEN="NAoa1I5OLykxUeYaGEy1g864"

# Delete outdated projects
echo '\n🗑️ Deleting outdated projects...'
echo 'Deleting orchestra-dev...'
# vercel remove orchestra-dev --yes || true

echo 'Deleting orchestra-admin-interface...'
# vercel remove orchestra-admin-interface --yes || true

echo 'Deleting v0-image-analysis...'
# vercel remove v0-image-analysis --yes || true

echo 'Deleting dist...'
# vercel remove dist --yes || true

echo 'Deleting react_app...'
# vercel remove react_app --yes || true

echo 'Deleting cherrybaby-mdzw...'
# vercel remove cherrybaby-mdzw --yes || true


# Create projects
echo '\n➕ Createing projects...'

# orchestra-dashboard
echo '\nProcessing orchestra-dashboard...'
cd dashboard
echo 'Creating vercel.json...'
cat > vercel.json << 'EOF'
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "functions": {
    "app/api/[...route]/route.ts": {
      "maxDuration": 10
    }
  }
}
EOF
echo 'Deploying to Vercel...'
npx vercel --prod --yes --name orchestra-dashboard
cd ..

# Update projects
echo '\n🔄 Updateing projects...'

# admin-interface
echo '\nProcessing admin-interface...'
cd admin-interface
echo 'Deploying to Vercel...'
npx vercel --prod --yes --name admin-interface
cd ..

# orchestra-ai-frontend
echo '\nProcessing orchestra-ai-frontend...'
cd src/ui/web/react_app
echo 'Deploying to Vercel...'
npx vercel --prod --yes --name orchestra-ai-frontend
cd ..
cd ../../../

echo "\n✅ Vercel Rebuild Complete!"
echo "============================"
echo ""
echo "📝 Next Steps:"
echo "1. Check deployments at https://vercel.com/dashboard"
echo "2. Update DNS/aliases as needed"
echo "3. Test all deployments"
