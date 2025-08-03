#!/bin/bash

# Script to publish the Telegram Broadcasting Bot to GitHub

echo "Publishing Telegram Broadcasting Bot to GitHub..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: This script must be run from the telegram-broadcast-dmbot directory"
    exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed"
    exit 1
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI is not installed"
    exit 1
fi

echo "Please follow these steps to publish the repository to GitHub:"

echo "
1. Create a new repository on GitHub:
   - Go to https://github.com/strad-dev131
   - Click on 'New' to create a new repository
   - Name the repository 'telegram-broadcast-dmbot'
   - Make it public or private as desired
   - Do NOT initialize with a README, .gitignore, or license
   - Click 'Create repository'

2. Run the following commands in your terminal:
   cd telegram-broadcast-dmbot
   git remote add origin https://github.com/strad-dev131/telegram-broadcast-dmbot.git
   git branch -M main
   git push -u origin main

3. If you have two-factor authentication enabled on your GitHub account, you'll need to use a personal access token instead of your password when pushing.

4. To create a personal access token:
   - Go to GitHub Settings
   - Click on 'Developer settings'
   - Click on 'Personal access tokens'
   - Click 'Generate new token'
   - Give it a name like 'telegram-broadcast-dmbot'
   - Select the 'repo' scope
   - Click 'Generate token'
   - Copy the token and use it as your password when pushing

That's it! Your repository should now be published to GitHub.
"

echo "Alternatively, if you have GitHub CLI authenticated, you can run:"
echo "gh repo create strad-dev131/telegram-broadcast-dmbot --public --push --source=. --remote=origin"
