#!/bin/bash

# ==============================================================================
# GCP VM Initial Startup Script (v3 - Git-driven)
#
# This script runs ONCE when the VM is first created. It sets up the
# environment by cloning the repository and launching the Docker stack.
# All subsequent updates should be done using the `redeploy.sh` script.
# ==============================================================================

set -e

# --- Configuration ---
# Replace this with your actual Git repository URL
GIT_REPO_URL="https://github.com/HaoweiChan/FreqTrade.git"
PROJECT_DIR="/home/freqtrade/freqtrade"

# Log everything to a file for debugging
exec > >(tee -a /var/log/startup-script.log)
exec 2>&1

echo "Starting Freqtrade Git-driven setup script..."
echo "Timestamp: $(date)"

# --- 1. System Dependencies ---
echo "Installing Git, Docker, and Docker Compose..."
apt-get update -y && apt-get upgrade -y
apt-get install -y git apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# --- 2. Freqtrade User and Directory Setup ---
echo "Configuring Freqtrade environment..."
useradd -m -s /bin/bash freqtrade || true # Fails gracefully if user exists
usermod -aG docker freqtrade

# --- 3. Clone the Repository ---
echo "Cloning repository from ${GIT_REPO_URL}..."
mkdir -p /home/freqtrade
git clone "${GIT_REPO_URL}" "${PROJECT_DIR}"
chown -R freqtrade:freqtrade /home/freqtrade

# Switch to the project directory
cd "${PROJECT_DIR}"

# --- 4. Initial Launch of the Freqtrade Stack ---
echo "Performing initial build of Docker images on the VM..."
docker-compose build

echo "Starting Freqtrade stack for the first time..."
docker-compose up -d

# --- 5. Systemd Service for Auto-Start on Boot ---
# This ensures that if the VM reboots, Docker Compose will restart your containers.
echo "Creating systemd service to manage Freqtrade on boot..."
cat > /etc/systemd/system/freqtrade.service << EOF
[Unit]
Description=Freqtrade Multi-Container Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=freqtrade
WorkingDirectory=${PROJECT_DIR}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target
EOF

systemctl enable freqtrade.service

echo "✅ Freqtrade initial setup completed successfully!"
echo "Timestamp: $(date)"
