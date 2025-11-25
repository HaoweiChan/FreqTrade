#!/bin/bash
set -e

# This script is executed on the remote VM to set up the environment and deploy
# It expects necessary environment variables to be set by the caller or substituted

# Required variables (passed via env):
# TARGET_USER
# PROJECT_DIR
# REPO_URL
# DOCKER_REGISTRY
# GITHUB_TOKEN
# GITHUB_ACTOR
# GITHUB_REF
# GITHUB_SHA
# DRY_RUN flags...

echo "🔧 Setting up deployment environment on VM..."

# Ensure target directory exists
if [ ! -d "$PROJECT_DIR" ]; then
  echo "📂 Creating project directory: $PROJECT_DIR"
  sudo mkdir -p "$PROJECT_DIR"
  sudo chown -R "$TARGET_USER":"$TARGET_USER" "$PROJECT_DIR"
fi

# Allow git to trust this directory (global config for the target user context)
git config --global --add safe.directory "$PROJECT_DIR" >/dev/null 2>&1 || true

if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "⚠️  Git metadata missing - cloning repository..."
  # Clear dir just in case
  rm -rf "$PROJECT_DIR"
  mkdir -p "$PROJECT_DIR"
  git clone "$REPO_URL" "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Ensure remote is correct
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
if [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
  echo "🔁 Updating remote URL to $REPO_URL"
  git remote set-url origin "$REPO_URL"
fi

echo "📥 Syncing repository..."
git fetch origin main --tags --prune
git checkout main
git reset --hard origin/main

echo "🔐 Authenticating to Registry..."
if ! printf '%s\n' "$GITHUB_TOKEN" | docker login "$DOCKER_REGISTRY" -u "$GITHUB_ACTOR" --password-stdin; then
  echo "❌ Docker login failed."
  exit 1
fi

# Determine image tag and env
if [[ "$GITHUB_REF" =~ ^refs/tags/v ]]; then
  export IMAGE_TAG="${GITHUB_REF#refs/tags/}"
  export DEPLOYMENT_ENV="production"
else
  export IMAGE_TAG="main-$(echo "$GITHUB_SHA" | cut -c1-7)"
  export DEPLOYMENT_ENV="staging"
fi

echo "🏷️  Deployment: $DEPLOYMENT_ENV with tag: $IMAGE_TAG"

# Export dry run variables for the deploy script
export ICHI_DRY_RUN LOOKAHEAD_DRY_RUN MACD_DRY_RUN PSAR_DRY_RUN MACDCCI_DRY_RUN

echo "🚀 Executing deployment script..."
chmod +x scripts/deploy.sh
if ! bash scripts/deploy.sh; then
  echo "❌ Deployment script failed."
  exit 1
fi

echo "--- ✅ Deployment on GCP VM Succeeded ---"

