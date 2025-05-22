#!/bin/bash
set -e

# Ensure we are on main
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
  echo "Switching to main branch..."
  git checkout main
fi

echo "\nCurrent branch: $(git rev-parse --abbrev-ref HEAD)"

echo "\nListing all local branches:"
git branch

echo "\nDeleting all local branches except main..."
for branch in $(git branch | grep -v 'main' | sed 's/^[* ]*//'); do
  git branch -d "$branch" || true
  echo "Deleted local branch: $branch"
done

echo "\nListing all remote branches:"
git branch -r

echo "\nYou can delete remote branches with: git push origin --delete <branch>"
echo "(Manual step to avoid accidental deletion of important branches.)"

echo "\nStaging and committing all changes..."
git add .
git commit -m "Consolidate to single-branch workflow; clean up for solo dev" || echo "No changes to commit."
git push origin main

echo "\nIf you want to tag a release, run:"
echo "git tag v1.0.0 && git push origin v1.0.0"

echo "\nDone! You are now set up for a clean solo workflow on main." 