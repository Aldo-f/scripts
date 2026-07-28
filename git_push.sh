#!/usr/bin/env bash

# Auto-push changes to the GitHub repo
# This script is intended to be run via cron after the health check.

set -euo pipefail

# --- Configuration ---
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="~/scripts/git_push.log"
GIT_USER=" Aldo"
GIT_EMAIL="aldo.fieuw@gmail.com"

cd "$REPO_DIR" || exit 1

# --- Setup Git (only if not already configured) ---
if ! git config --get user.name > /dev/null 2>&1; then
    git config user.name "$GIT_USER"
fi
if ! git config --get user.email > /dev/null 2>&1; then
    git config user.email "$GIT_EMAIL"
fi

# --- Stage and commit changes ---
git add .
# Look for meaningful changes to commit; skip if nothing changed
if ! git diff --cached --quiet; then
    TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
    git commit -m "Auto-commit $TIMESTAMP — health check update"
fi

# --- Pull any remote updates (force with --allow-unsafe-overrides) ---
#       This avoids a "non-fast-forward" error when merging forked repos.
git pull --allow-unsafe-overrides origin main

# --- Push changes ---
#       Using --force-with-lease for safety while allowing updates.
git push origin main --force-with-lease 2>&1 | tee "$LOG_FILE"

# --- End of script ---
