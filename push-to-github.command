#!/bin/bash
# Push Dick Wray Website to GitHub
# Double-click this file in Finder to run it

cd "$(dirname "$0")"
SITE_DIR="$(pwd)"

echo "================================================"
echo "  Dick Wray Website — Push to GitHub"
echo "================================================"
echo ""

# Fresh start — wipe old git history (removes commits that contained secrets)
echo "Initializing clean git repository..."
rm -rf .git
git init -b main
echo ""

# Set remote (public URL for committed file — token used only at push time)
REPO_URL="https://github.com/robertwrayscode/Dickwray-Website.git"
if ! git remote get-url origin > /dev/null 2>&1; then
    git remote add origin "$REPO_URL"
    echo "Remote set to: $REPO_URL"
elif [ "$(git remote get-url origin)" != "$REPO_URL" ]; then
    git remote set-url origin "$REPO_URL"
    echo "Remote updated to: $REPO_URL"
fi

echo ""
echo "Staging files..."

# Stage the clean static site files (not old PHP stuff)
git add \
    .gitignore \
    index.html cv.html essays.html interviews.html publications.html \
    watercolors.html black-and-whites.html early-works.html large-works.html \
    css/ js/main.js \
    assets/images/ \
    _data/ \
    admin-tool/ \
    push-to-github.command

echo ""

# Check if there's anything to commit
if git diff --cached --quiet 2>/dev/null; then
    if git log --oneline -1 > /dev/null 2>&1; then
        echo "No changes to commit. Everything is up to date."
    else
        echo "Creating initial commit..."
        git commit -m "Clean static site rebuild with local admin tool

Complete rebuild of Dick Wray portfolio site as a static site with a
local Python admin tool for image/content management and one-click deploy.

- Replaced all PHP with static HTML generated from Jinja2 templates
- Built Flask-based admin app with image/interview/publication management
- Consolidated duplicate CSS/JS, fixed inconsistent image paths
- 9 generated pages: index, cv, essays, interviews, publications, 4 collections
- Ready for GitHub Pages hosting

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
    fi
else
    echo "Committing changes..."
    git commit -m "Update Dick Wray website

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
fi

echo ""
echo "Pushing to GitHub..."
echo "(You may be prompted to log in to GitHub)"
echo ""

# Read token from .git-token file (not tracked by git)
if [ -f ".git-token" ]; then
    TOKEN=$(cat .git-token | tr -d '[:space:]')
    PUSH_URL="https://${TOKEN}@github.com/robertwrayscode/Dickwray-Website.git"
    git push -u --force "$PUSH_URL" main 2>&1
else
    echo "No .git-token file found. Create one with your GitHub Personal Access Token:"
    echo "  echo 'your_token_here' > .git-token"
    git push -u --force origin main 2>&1
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "  SUCCESS! Site pushed to GitHub."
    echo "  https://github.com/robertwrayscode/Dickwray-Website"
    echo "================================================"
    echo ""
    echo "Next step: Enable GitHub Pages in your repo settings"
    echo "  Settings → Pages → Source: Deploy from branch → main → / (root)"
    echo ""
    echo "Your site will be live at:"
    echo "  https://robertwrayscode.github.io/Dickwray-Website/"
    echo ""
    echo "To point www.dickwray.com to it, we'll set up a custom domain."
else
    echo ""
    echo "Push failed. You may need to:"
    echo "  1. Create the repo first: https://github.com/new"
    echo "     Name: Dickwray-Website"
    echo "     Make it Public"
    echo "     Don't add README or .gitignore"
    echo "  2. Run this script again"
fi

echo ""
echo "Press any key to close..."
read -n 1
