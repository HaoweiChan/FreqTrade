# Freqtrade Deployment Scripts

This directory contains scripts for managing Freqtrade deployment.

## Scripts Overview

### `setup-strategies.sh`

**Purpose:** Generate `docker-compose.yml` from strategy list

**Usage:**
```bash
bash scripts/setup-strategies.sh
```

**What it does:**
- Reads strategy list from `STRATEGIES` array
- Generates unified `docker-compose.yml` 
- Creates `strategies.tar.gz` for Docker build
- Configures ports, environment variables, and container names

**When to use:**
- After adding/removing strategies
- When modifying strategy configuration
- Initial project setup

---

### `deploy.sh`

**Purpose:** Unified deployment script for local and GCP

**Usage:**
```bash
# Local development (builds from source)
bash scripts/deploy.sh

# Local testing (pulls production images)
bash scripts/deploy.sh --pull

# GCP production (automatically pulls)
# Run on GCP VM - auto-detects environment
bash scripts/deploy.sh
```

**What it does:**

**Local Mode:**
- Default: Builds images from source
- With `--pull`: Pulls pre-built images from registry
- Stops existing containers
- Starts services with docker-compose

**GCP Mode** (auto-detected):
- Pulls latest code from git
- Pulls images from registry (never builds)
- Stops existing services
- Starts services in background
- Cleans up old images

**Environment Detection:**
- Checks for `$GCP_PROJECT`, `$GOOGLE_CLOUD_PROJECT`, or GCP metadata
- Automatically chooses appropriate deployment strategy

---

## Deployment Workflows

### Initial Setup

```bash
# 1. Generate docker-compose.yml
bash scripts/setup-strategies.sh

# 2. Deploy locally
bash scripts/deploy.sh
```

### Local Development

```bash
# Make code changes
vim user_data/strategies/MyStrategy.py

# Rebuild and deploy
bash scripts/deploy.sh
```

### Testing Production Images Locally

```bash
# Pull and test exact images from CI/CD
export DOCKER_REGISTRY=ghcr.io
export REPO_NAME=YOUR_USERNAME/freqtrade
export IMAGE_TAG=main-abc123

bash scripts/deploy.sh --pull
```

### GCP Deployment

```bash
# SSH to GCP VM
gcloud compute ssh freqtrade-bot --zone=asia-east1-b

# Deploy (auto-detects GCP and pulls images)
cd freqtrade
bash scripts/deploy.sh
```

## Environment Variables

### Registry Configuration

```bash
# Used by deploy.sh when pulling images
DOCKER_REGISTRY=ghcr.io                    # Registry URL
REPO_NAME=YOUR_USERNAME/freqtrade          # Repository name
IMAGE_TAG=latest                           # Image tag (or SHA)
```

### Trading Configuration

```bash
# Used by docker-compose.yml
BINANCE_KEY=your_api_key
BINANCE_SECRET=your_api_secret
TELEGRAM_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
FT_UI_USERNAME=admin
FT_UI_PASSWORD=your_password
```

## Script Maintenance

### Adding a New Strategy

1. Edit `scripts/setup-strategies.sh`
2. Add strategy name to `STRATEGIES` array
3. Run: `bash scripts/setup-strategies.sh`
4. Deploy: `bash scripts/deploy.sh`

### Modifying Deployment Logic

Edit `scripts/deploy.sh` - single file handles all deployment scenarios:
- Local build mode
- Local pull mode  
- GCP production mode

## Troubleshooting

### Script Fails: "command not found"

```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Docker Compose Not Found

```bash
# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Registry Authentication Failed

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

### GCP Auto-Detection Not Working

```bash
# Manually set environment
export GCP_PROJECT=your-project-id
bash scripts/deploy.sh
```

## Best Practices

1. **Always run `setup-strategies.sh` after strategy changes**
2. **Use `--pull` flag locally to test production images**
3. **Never build on GCP** - always pull from registry
4. **Test locally before deploying to GCP**
5. **Use specific image tags (SHA) in production**, not `latest`

## Quick Reference

```bash
# Setup
bash scripts/setup-strategies.sh          # Generate docker-compose.yml

# Deploy
bash scripts/deploy.sh                    # Local: build, GCP: pull
bash scripts/deploy.sh --pull             # Local: pull images

# Docker operations
docker-compose ps                         # Check status
docker-compose logs -f                    # View logs
docker-compose restart SERVICE            # Restart service
docker-compose down                       # Stop all
```

## See Also

- [Main README](../README.md) - Comprehensive documentation
- [docker-compose.yml](../docker-compose.yml) - Generated configuration
- [Dockerfile](../Dockerfile) - Bot image definition
- [ui/Dockerfile](../ui/Dockerfile) - UI image definition
