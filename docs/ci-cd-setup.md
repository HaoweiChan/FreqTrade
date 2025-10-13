# CI/CD Pipeline Setup Guide

This document explains how to set up the GitHub Actions CI/CD pipeline for your Freqtrade project.

## Pipeline Overview

The CI/CD pipeline includes:

1. **Build & Test Trading Bot**: Builds the main Freqtrade Docker image and tests it runs correctly
2. **Build & Test UI**: Builds the FreqUI Docker image and tests web interface accessibility 
3. **Integration Test**: Tests the full docker-compose stack with multiple services
4. **Security Scan**: Scans Docker images for vulnerabilities using Trivy
5. **Deploy to GCP**: Automatically deploys to GCP VM on main branch pushes

## Required GitHub Secrets

To enable the full pipeline, configure these secrets in your GitHub repository settings:

### Trading Configuration
```
BINANCE_KEY=your_binance_api_key_here
BINANCE_SECRET=your_binance_secret_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
FT_UI_USERNAME=your_ui_username_here
FT_UI_PASSWORD=your_ui_password_here
```

### GCP Deployment (Production Environment)
```
GCP_PROJECT_ID=your-gcp-project-id
GCP_SA_KEY=your-gcp-service-account-json-key
GCP_SSH_PRIVATE_KEY=your-ssh-private-key-for-vm
GCP_VM_IP=your-gcp-vm-external-ip
GCP_VM_USER=your-gcp-vm-username
```

## Pipeline Triggers

The pipeline runs on:
- **Push to main/develop**: Full pipeline including deployment (main only)
- **Pull requests to main**: Build and test only, no deployment
- **Manual trigger**: Via GitHub Actions "Run workflow" button

## What Each Job Does

### 1. Build & Test Trading Bot
- Builds the main Dockerfile with trading strategies
- Pushes image to GitHub Container Registry (ghcr.io)
- Tests the image runs in dry-run mode without crashing

### 2. Build & Test UI
- Builds the FreqUI interface from ui/Dockerfile
- Pushes UI image to GitHub Container Registry
- Tests that the web interface serves content correctly

### 3. Integration Test
- Creates a test docker-compose configuration
- Builds and starts the full stack (bot + UI)
- Verifies services start correctly and UI is accessible

### 4. Security Scan
- Runs Trivy vulnerability scanner on the trading bot image
- Uploads results to GitHub Security tab for review

### 5. Deploy to GCP (Production)
- Only runs on main branch pushes
- SSHs into your GCP VM
- Pulls latest code and rebuilds/restarts services
- Verifies deployment was successful

## GCP VM Prerequisites

Your GCP VM should have:
1. Docker and docker-compose installed
2. Git repository cloned at `/home/{user}/freqtrade`
3. SSH access configured for the deployment key
4. Proper firewall rules for the trading bot ports

## Local Development

For local development, you can:
```bash
# Build and test locally
docker-compose build
docker-compose up -d

# Or use the existing local deployment script
./scripts/deploy-local.sh
```

## Monitoring

After deployment, you can monitor:
- **GitHub Actions**: Check pipeline status and logs
- **GitHub Security**: Review vulnerability scan results  
- **GCP VM**: SSH in and run `docker-compose ps` to check service status
- **FreqUI**: Access via `http://YOUR_VM_IP:8080` to monitor trading

## Troubleshooting

### Pipeline Fails on Build
- Check Dockerfile syntax and dependencies
- Verify all required files are committed to git
- Check GitHub Actions logs for specific error messages

### Deployment Fails
- Verify all GCP secrets are configured correctly
- Check GCP VM is running and accessible
- Ensure SSH key has correct permissions
- Verify freqtrade directory exists on VM

### Trading Bot Fails to Start
- Check .env file on GCP VM has correct API keys
- Verify Binance API permissions and sandbox settings
- Check docker-compose logs for specific error messages

## Security Notes

- Never commit real API keys or secrets to git
- Use GitHub environments to restrict deployment access
- Regularly rotate API keys and SSH keys
- Monitor vulnerability scan results and update base images
