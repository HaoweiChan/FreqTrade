#!/bin/bash

# Local Deployment Script for Freqtrade Multi-Container Stack
# Combines testing and deployment tasks into a single workflow.

set -e

# Color definitions for user-friendly output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

printf "%b\n" "${GREEN}Building and launching Freqtrade stack locally${NC}"
printf "\n"

# Check if env.local exists, create if not
if [ ! -f "env.local" ]; then
    printf "%b\n" "${YELLOW}Creating env.local file with default values...${NC}"
    cat > env.local << 'EOF'
# Local Development Environment Variables
UI_IMAGE=freqtrade-ui:latest
TRADER_IMAGE=freqtrade-trader:latest
UI_PORT=8080
PORT_ICHIV1=8081
PORT_LOOKAHEAD=8082
PORT_MACD=8083
PORT_CUSTOMSTOPLOSS=8084
PORT_MACDCCI=8085
USER_DATA_PATH=./user_data
EOF
fi

# Stop any running containers from previous runs
printf "%b\n" "${YELLOW}Stopping existing containers (if any)...${NC}"
docker-compose --env-file env.local down 2>/dev/null || true

# Build images and start containers defined in docker-compose.yml
printf "%b\n" "${YELLOW}Building images and starting containers...${NC}"
docker-compose --env-file env.local up --build -d

# Wait for containers to finish initialising
printf "%b\n" "${YELLOW}Waiting for containers to start...${NC}"
sleep 10

# Verify that all services are up
if docker-compose --env-file env.local ps | grep -q "Up"; then
    printf "%b\n" "${GREEN}All containers are running!${NC}"
else
    printf "%b\n" "${RED}Some containers failed to start. Check logs below:${NC}"
    docker-compose --env-file env.local ps
    exit 1
fi

printf "\n"
printf "%b\n" "${YELLOW}Management commands:${NC}"
echo "  View logs: docker-compose --env-file env.local logs -f"
echo "  Stop: docker-compose --env-file env.local down"
echo "  Restart: docker-compose --env-file env.local restart"
echo "  View services: docker-compose --env-file env.local ps"

printf "\n"
printf "%b\n" "${GREEN}Stack is up and running locally!${NC}" 