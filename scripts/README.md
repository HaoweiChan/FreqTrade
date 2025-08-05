# Freqtrade Deployment Scripts

This directory contains the scripts needed to deploy your freqtrade strategies to Google Cloud Platform.

## Scripts

### `setup-strategies.sh`
**Purpose**: Prepares your deployment configuration
**What it does**:
- ✅ Verifies your top 20 strategies exist in `user_data/strategies/`
- ✅ Creates `docker-compose.yml` with your top strategies configured
- ✅ Prepares deployment configuration for GCP

**Usage**:
```bash
scripts/setup-strategies.sh
```

### `deploy-gcp.sh` 
**Purpose**: Deploys freqtrade to Google Cloud Platform
**What it does**:
- ✅ Creates GCP VM instance with Ubuntu 24.04 LTS
- ✅ Deploys your config.json (API keys, trading settings)
- ✅ Deploys all your strategies (400+ files)
- ✅ Deploys your docker-compose.yml with top 20 strategies
- ✅ Sets up firewall rules and security

**Usage**:
```bash
scripts/deploy-gcp.sh
```

### `startup-script.sh`
**Purpose**: VM initialization script (runs automatically on GCP VM)
**What it does**:
- ✅ Installs Docker and Docker Compose on the VM
- ✅ Extracts and configures your files from metadata
- ✅ Starts freqtrade with your configuration
- ✅ Sets up systemd service for auto-restart

**Note**: This script runs automatically during VM creation.

## Deployment Workflow

1. **Setup**: `scripts/setup-strategies.sh`
2. **Deploy**: `scripts/deploy-gcp.sh`
3. **Access**: Your freqtrade UI at `http://EXTERNAL_IP:8080`

## Configuration

All scripts are pre-configured for your setup:
- **Project ID**: oceanic-glazing-466419-v3
- **Zone**: asia-east1-b (optimal for Binance)
- **Instance**: freqtrade-bot (e2-medium, 2 vCPU, 4GB RAM) 