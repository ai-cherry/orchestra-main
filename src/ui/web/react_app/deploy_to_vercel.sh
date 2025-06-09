#!/usr/bin/env bash

# Force Vercel to use the current directory as project root
# This fixes the path error by explicitly setting the project root

# Deploy to Vercel non-interactively with cwd flag
vercel --token NAoa1I5OLykxUeYaGEy1g864 --cwd . --yes

# Output deployment URL
echo "Deployment complete. Visit the URL above to view your site."
