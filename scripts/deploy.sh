#!/bin/bash

# Configuration
BRANCH="gh-pages"
FOLDER="output"

echo "🚀 Starting Deployment to GitHub Pages..."

# 1. Check if git is clean (recommended but we will force add for user convenience)
git add .
git commit -m "Deploy: Update site content for GitHub Pages"

# 2. Push the subtree
echo "📦 Pushing '$FOLDER' folder to '$BRANCH' branch..."
git subtree push --prefix $FOLDER origin $BRANCH

if [ $? -eq 0 ]; then
  echo "✅ Deployment Successful!"
  echo "🌍 Your site should be live at: https://[username].github.io/[repo-name]/"
else
  echo "❌ Deployment Failed. Check if 'origin' is set correctly."
fi
