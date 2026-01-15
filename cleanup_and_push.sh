#!/bin/bash
echo "🧹 Cleaning up GitHub repository..."
echo ""

# Remove personal files from Git tracking (but keep locally)
echo "📝 Removing personal files from Git tracking..."
git rm --cached DOCKER_FIX.md DOCKERFILE_UPDATES.md FRONTEND_BACKEND_SEPARATION.md progress.md GITHUB_READY.md PRE_COMMIT_CHECKLIST.md main.py.old 2>/dev/null || true

# Add updated .gitignore and other changes
echo "📦 Staging changes..."
git add .

# Show what will be committed
echo ""
echo "📋 Changes to be committed:"
git status --short

echo ""
read -p "Continue with commit? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "Clean up: Remove personal files from Git tracking and update .gitignore"
    echo ""
    echo "🚀 Pushing to GitHub..."
    git push origin main
    echo ""
    echo "✅ Done! Files removed from GitHub but kept locally."
else
    echo "❌ Cancelled. Run 'git reset' to unstage changes."
fi
