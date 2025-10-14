#!/bin/bash
set -e

# This script is designed to be run on a production-like environment
# where the code has already been checked out and required environment
# variables (like IMAGE_TAG and credentials) are already set.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for logging
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Freqtrade Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

cd "$PROJECT_ROOT"

# Verify that IMAGE_TAG is set
if [ -z "$IMAGE_TAG" ]; then
  echo -e "${YELLOW}Warning: IMAGE_TAG is not set. Defaulting to 'latest'.${NC}"
  export IMAGE_TAG="latest"
fi
echo -e "${YELLOW}📦 Using image tag: ${IMAGE_TAG}${NC}"
echo ""

echo -e "${GREEN}Step 1: Stopping current services...${NC}"
docker-compose down
echo ""

echo -e "${GREEN}Step 2: Pulling latest images from registry...${NC}"
# The docker-compose.yml file will use the IMAGE_TAG variable
docker-compose pull
echo ""

echo -e "${GREEN}Step 3: Rebuilding UI with latest code changes...${NC}"
# Rebuild UI without cache to ensure init-bots.js changes are applied
docker-compose build --no-cache frequi
echo ""

echo -e "${GREEN}Step 4: Starting services...${NC}"
# Start all services
docker-compose up -d
echo ""

echo -e "${GREEN}Step 5: Verifying deployment status...${NC}"
# Wait for services to initialize
sleep 15
docker-compose ps
echo ""

echo -e "${GREEN}Step 6: Cleaning up old Docker images...${NC}"
docker image prune -f
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

