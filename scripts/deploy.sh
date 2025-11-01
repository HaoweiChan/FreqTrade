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

# Set port configuration based on deployment environment
# Default to production ports (8080-8085)
if [ -z "$DEPLOYMENT_ENV" ]; then
  export DEPLOYMENT_ENV="production"
fi

if [ "$DEPLOYMENT_ENV" = "staging" ]; then
  echo -e "${YELLOW}🏷️  Deployment environment: STAGING (using ports 9080-9085)${NC}"
  export UI_PORT=9080
  export BOT_PORT_ICHI=9081
  export BOT_PORT_LOOKAHEAD=9082
  export BOT_PORT_MACD=9083
  export BOT_PORT_PSAR=9084
  export BOT_PORT_MACDCCI=9085
else
  echo -e "${YELLOW}🏷️  Deployment environment: PRODUCTION (using ports 8080-8085)${NC}"
  export UI_PORT=${UI_PORT:-8080}
  export BOT_PORT_ICHI=${BOT_PORT_ICHI:-8081}
  export BOT_PORT_LOOKAHEAD=${BOT_PORT_LOOKAHEAD:-8082}
  export BOT_PORT_MACD=${BOT_PORT_MACD:-8083}
  export BOT_PORT_PSAR=${BOT_PORT_PSAR:-8084}
  export BOT_PORT_MACDCCI=${BOT_PORT_MACDCCI:-8085}
fi
echo ""

echo -e "${GREEN}Step 1: Stopping current services...${NC}"
docker-compose down
echo ""

echo -e "${GREEN}Step 2: Pulling latest images from registry...${NC}"
# The docker-compose.yml file will use the IMAGE_TAG variable
docker-compose pull
echo ""

echo -e "${GREEN}Step 3: Starting services with pulled images...${NC}"
# Start all services using pulled images (no rebuild)
docker-compose up -d
echo ""

echo -e "${GREEN}Step 4: Verifying deployment status...${NC}"
# Wait for services to initialize
sleep 15
docker-compose ps
echo ""

echo -e "${GREEN}Step 5: Cleaning up old Docker images...${NC}"
docker image prune -f
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

