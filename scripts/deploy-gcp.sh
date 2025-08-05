#!/bin/bash

# ==============================================================================
# Freqtrade GCP Initial Provisioning Script (v4 - Git-driven)
#
# This script provisions a new GCP VM and runs the initial setup script.
# It is meant to be run ONLY ONCE for the initial creation of the VM.
# All subsequent code deployments should be done by SSH'ing into the VM
# and running the `scripts/redeploy.sh` script.
# ==============================================================================

set -e

# --- Configuration ---
PROJECT_ID="oceanic-glazing-466419-v3"
REGION="asia-east1"
ZONE="asia-east1-b"
INSTANCE_NAME="freqtrade-bot"
MACHINE_TYPE="e2-medium"
IMAGE_FAMILY="ubuntu-24-04-lts"
IMAGE_PROJECT="ubuntu-os-cloud"

# --- Colors for output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting Freqtrade GCP VM Provisioning...${NC}"

# --- Step 1: Prerequisites Check ---
echo -e "\n${YELLOW}Step 1: Checking gcloud CLI...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ GCloud CLI is ready.${NC}"

# --- Step 2: Deploy VM Instance ---
echo -e "\n${YELLOW}Step 2: Provisioning Google Compute Engine VM...${NC}"

if gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE &> /dev/null; then
    echo "Instance '$INSTANCE_NAME' already exists. Deleting for a fresh deployment..."
    gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet
fi

echo "Creating new VM instance '$INSTANCE_NAME'..."
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=freqtrade,http-server \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=50GB \
    --metadata-from-file startup-script=scripts/startup-script.sh

echo "Creating firewall rule for IAP TCP Forwarding..."
gcloud compute firewall-rules create allow-iap-tcp-forwarding \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:22,tcp:80 \
    --source-ranges=35.235.240.0/20 \
    --target-tags=freqtrade \
    --description="Allow IAP TCP forwarding for SSH and Freqtrade UI" --quiet || true

# --- Step 3: Finalizing ---
echo -e "\n${YELLOW}Step 3: Waiting for instance to initialize... (This may take a few minutes for the initial build)${NC}"
sleep 180 # Give it enough time to clone, build, and start

echo -e "\n${GREEN}✅ VM Provisioning complete!${NC}"
echo -e "\n${YELLOW}Your new Git-driven DevOps pipeline is ready.${NC}"
echo -e "1. ${GREEN}To deploy future code changes:${NC}"
echo -e "   - First, commit and push your changes to your Git repository."
echo -e "   - Then, SSH into your VM:"
echo -e "     gcloud compute ssh freqtrade-bot --zone=${ZONE}"
echo -e "   - And run the redeployment script:"
echo -e "     cd freqtrade && ./scripts/redeploy.sh"
echo -e "\n2. ${GREEN}To access your Freqtrade UI:${NC}"
echo -e "   gcloud compute start-iap-tunnel ${INSTANCE_NAME} 80 --zone=${ZONE} --local-host-port=localhost:8080"
echo -e "   Then open: ${GREEN}http://localhost:8080${NC}"
