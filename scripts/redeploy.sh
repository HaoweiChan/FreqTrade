#!/bin/bash

# ==============================================================================
# Freqtrade Redeployment Script (to be run on the GCP VM)
#
# This script pulls the latest code from the Git repository and rebuilds
# and restarts the Docker stack.
# ==============================================================================

set -e

# --- Colors for output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting Freqtrade redeployment...${NC}"

# 1. Pull latest code from Git
echo -e "\n${GREEN}Step 1: Pulling latest changes from Git...${NC}"
git pull origin main

# 2. Stop the currently running services
echo -e "\n${GREEN}Step 2: Stopping current services...${NC}"
docker-compose down

# 3. Build fresh Docker images on the VM
# This automatically uses the correct amd64 architecture.
echo -e "\n${GREEN}Step 3: Building new Docker images...${NC}"
docker-compose build

# 4. Start the new services in the background
echo -e "\n${GREEN}Step 4: Starting new services...${NC}"
docker-compose up -d

# 5. Clean up old, unused Docker images
echo -e "\n${GREEN}Step 5: Pruning old Docker images...${NC}"
docker image prune -f

echo -e "\n${GREEN}✅ Redeployment complete!${NC}"
