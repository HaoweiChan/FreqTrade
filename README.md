# Freqtrade Unified Deployment

![Freqtrade](https://img.shields.io/badge/Freqtrade-Trading%20Bot-blue)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![GCP](https://img.shields.io/badge/GCP-Cloud%20Deploy-green)

> **Unified Docker Compose approach** - One configuration file for local development and GCP production

## 🚀 Quick Start

### Local Development (Build from Source)

```bash
# 1. Clone and setup
git clone https://github.com/haowiechan/freqtrade.git
cd freqtrade

# 2. Create environment file from template
cp .env.example .env

# 3. Generate docker-compose.yml
bash scripts/setup-strategies.sh

# 4. Start services (builds locally)
docker-compose up --build

# 5. Access FreqUI
# Open: http://localhost:8080
# Login: admin / admin123
```

### GCP Production (Pull from Registry)

```bash
# 1. SSH to GCP VM
gcloud compute ssh freqtrade-bot --zone=asia-east1-b

# 2. Deploy (automatically detects GCP and pulls from registry)
cd freqtrade
bash scripts/deploy.sh

# 3. Access via IAP tunnel (from local machine)
gcloud compute start-iap-tunnel freqtrade-bot 8080 \
  --local-host-port=localhost:9090 --zone=asia-east1-b

# Open: http://localhost:9090
```

## 📁 Project Structure

```
freqtrade/
├── scripts/
│   ├── setup-strategies.sh     # Generate docker-compose.yml
│   └── deploy.sh               # Unified deployment (local & GCP)
├── user_data/
│   ├── config.json             # Trading configuration
│   ├── strategies/             # Your trading strategies
│   ├── data/                   # Market data
│   └── logs/                   # Trading logs
├── docker-compose.yml          # Unified configuration (auto-generated)
├── Dockerfile                  # Bot image definition
├── ui/Dockerfile               # UI image definition
└── .env.example                # Environment template (copy to .env)
```

## 🎯 Unified Deployment Approach

The unified approach uses **one docker-compose.yml** that works everywhere:

### How It Works

```yaml
services:
  frequi:
    image: ${DOCKER_REGISTRY:-ghcr.io}/${REPO_NAME:-haowiechan/freqtrade}/freqtrade-ui:${IMAGE_TAG:-latest}
    build:
      context: ./ui
      dockerfile: Dockerfile
```

**Behavior:**
- **Empty env vars** → Builds locally (fast iteration)
- **Set env vars** → Pulls from registry (production mode)

### Deployment Comparison

| Aspect | Local Development | GCP Production |
|--------|------------------|----------------|
| Config File | docker-compose.yml | docker-compose.yml ✅ Same |
| Image Source | Build locally OR Pull | Always pull from CI/CD |
| Command | `docker-compose up --build` | `docker-compose pull && up` |
| Speed | Fast (cached) | Very fast (no build) |
| Consistency | Fresh builds | CI/CD tested images |

## 🔐 Setting Up Image Registry

### Option 1: GitHub Container Registry (Recommended)

#### 1. Create GitHub Personal Access Token (PAT)

```bash
# Go to: https://github.com/settings/tokens
# Click: Generate new token (classic)
# Scopes: read:packages, write:packages, delete:packages
# Copy the token
```

#### 2. Authenticate Docker with GHCR

```bash
# Local machine
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# On GCP VM (for deployment)
gcloud compute ssh freqtrade-bot --zone=asia-east1-b
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

#### 3. Configure CI/CD Pipeline

Your `.github/workflows/ci-cd.yml` already builds and pushes to GHCR:

```yaml
env:
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME_BOT: ${{ github.repository }}/freqtrade-bot
  IMAGE_NAME_UI: ${{ github.repository }}/freqtrade-ui
```

**No changes needed!** The pipeline automatically:
- Builds bot and UI images on push to main
- Tests the images
- Pushes to `ghcr.io/YOUR_USERNAME/freqtrade/freqtrade-bot:latest`
- Tags with SHA: `main-abc123` for rollback capability

#### 4. Verify Images are Pushed

```bash
# Check GitHub Packages
# Visit: https://github.com/YOUR_USERNAME?tab=packages

# Or pull manually to test
docker pull ghcr.io/YOUR_USERNAME/freqtrade/freqtrade-bot:latest
```

### Option 2: GCP Artifact Registry

#### 1. Create Artifact Registry Repository

```bash
# Set variables
export PROJECT_ID="your-gcp-project-id"
export REGION="asia-east1"

# Create repository
gcloud artifacts repositories create freqtrade-images \
  --repository-format=docker \
  --location=$REGION \
  --description="Freqtrade Docker images"
```

#### 2. Authenticate Docker with Artifact Registry

```bash
# Configure Docker authentication
gcloud auth configure-docker $REGION-docker.pkg.dev
```

#### 3. Update CI/CD to Push to GCP

Update `.github/workflows/ci-cd.yml`:

```yaml
env:
  DOCKER_REGISTRY: asia-east1-docker.pkg.dev
  IMAGE_NAME_BOT: YOUR_PROJECT_ID/freqtrade-images/freqtrade-bot
  IMAGE_NAME_UI: YOUR_PROJECT_ID/freqtrade-images/freqtrade-ui
```

Add GCP authentication step:

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    credentials_json: ${{ secrets.GCP_CREDENTIALS }}

- name: Set up Cloud SDK
  uses: google-github-actions/setup-gcloud@v1
```

#### 4. Add GCP Credentials to GitHub Secrets

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com

# Add to GitHub Secrets as GCP_CREDENTIALS
# Go to: https://github.com/YOUR_REPO/settings/secrets/actions
# Name: GCP_CREDENTIALS
# Value: <paste contents of key.json>
```

## 🔄 CI/CD Integration

### Automated Build and Deploy Flow

```
Code Push → GitHub Actions → Build & Test → Push to Registry
                                                  ↓
                      ┌───────────────────────────┴────────────────────┐
                      ↓                                                ↓
              Local Development                                  GCP Production
              (optional pull)                                    (always pull)
              docker-compose pull                               docker-compose pull
```

### Manual Build and Push

```bash
# Build images locally
docker build -t ghcr.io/YOUR_USERNAME/freqtrade/freqtrade-bot:latest .
docker build -t ghcr.io/YOUR_USERNAME/freqtrade/freqtrade-ui:latest ./ui

# Push to registry
docker push ghcr.io/YOUR_USERNAME/freqtrade/freqtrade-bot:latest
docker push ghcr.io/YOUR_USERNAME/freqtrade/freqtrade-ui:latest
```

## 🔧 Environment Configuration

### Environment File Setup

**Best Practice:**
1. `.env.example` - Template with dummy values ✅ **Commit this**
2. `.env` - Your actual secrets ❌ **Never commit** (in .gitignore)
3. Copy `.env.example` to `.env` and fill in real values

```bash
# Create your local environment file
cp .env.example .env

# Edit with your actual values
vim .env
```

### Local Development (.env for local builds)

```bash
# Empty = build locally (default)
DOCKER_REGISTRY=
REPO_NAME=
IMAGE_TAG=

# Trading credentials (use dummy for local testing)
BINANCE_KEY=test_key
BINANCE_SECRET=test_secret
TELEGRAM_TOKEN=test_token
TELEGRAM_CHAT_ID=test_id

# FreqUI auth (simple for local)
FT_UI_USERNAME=admin
FT_UI_PASSWORD=admin123

# Safe mode (recommended for local)
FREQTRADE__DRY_RUN=true
FREQTRADE__EXCHANGE__SANDBOX=true
```

### GCP Production (.env on VM)

**⚠️ Security:** Create `.env` on GCP VM - never commit real credentials!

```bash
# On GCP VM, create .env file
cat > .env <<EOF
# Pull from registry
DOCKER_REGISTRY=ghcr.io
REPO_NAME=YOUR_USERNAME/freqtrade
IMAGE_TAG=latest  # or specific SHA like main-abc123

# Real credentials (SET THESE!)
BINANCE_KEY=your_real_binance_key
BINANCE_SECRET=your_real_binance_secret
TELEGRAM_TOKEN=your_real_telegram_token
TELEGRAM_CHAT_ID=your_real_chat_id

# Strong password!
FT_UI_USERNAME=admin
FT_UI_PASSWORD=your_strong_password_here

# Production mode (adjust as needed)
FREQTRADE__DRY_RUN=true
FREQTRADE__EXCHANGE__SANDBOX=true
EOF

# Secure the file
chmod 600 .env
```

**💡 Tip:** Use GCP Secret Manager for production secrets:
```bash
# Store secrets
gcloud secrets create binance-api-key --data-file=-
# (paste key, then Ctrl+D)

# Retrieve in deployment
export BINANCE_KEY=$(gcloud secrets versions access latest --secret="binance-api-key")
```

## 📦 Deployment Workflows

### Local Development Workflow

```bash
# 1. Make code changes
vim user_data/strategies/my_strategy.py

# 2. Test locally
docker-compose up --build freqtrade-ichiv1

# 3. Commit and push
git commit -am "Update strategy"
git push origin main

# 4. CI/CD automatically builds and pushes to registry
```

### GCP Deployment Workflow

```bash
# 1. SSH to GCP VM
gcloud compute ssh freqtrade-bot --zone=asia-east1-b

# 2. Deploy (automatically pulls from registry)
cd freqtrade
bash scripts/deploy.sh

# Script automatically:
# - Detects GCP environment
# - Pulls latest code (git pull)
# - Pulls latest images (docker-compose pull)
# - Restarts services (docker-compose up -d)
# - Never builds on GCP!
```

### Testing Production Images Locally

```bash
# Pull and test exact same images as GCP
export DOCKER_REGISTRY=ghcr.io
export REPO_NAME=YOUR_USERNAME/freqtrade
export IMAGE_TAG=main-abc123  # Specific version

docker-compose pull
docker-compose up

# Access: http://localhost:8080
```

## 🛠️ Common Commands

```bash
# View running services
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific bot)
docker-compose logs -f freqtrade-ichiv1

# Restart specific bot
docker-compose restart freqtrade-ichiv1

# Stop all services
docker-compose down

# Deploy locally (build from source)
bash scripts/deploy.sh

# Deploy locally (pull production images for testing)
bash scripts/deploy.sh --pull

# Deploy on GCP (automatically pulls)
bash scripts/deploy.sh
```

## 🔍 Troubleshooting

### Bots Show "Login info expired!"

**Solution:** Log into each bot via FreqUI:
1. Click bot name → Configure
2. Enter username/password from .env file
3. Click "Save"

### "Image not found" Error

**Cause:** CI/CD hasn't run or authentication failed

**Solution:**
```bash
# Re-authenticate
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Check if image exists
docker pull ghcr.io/YOUR_USERNAME/freqtrade/freqtrade-bot:latest

# If doesn't exist, trigger CI/CD by pushing code
git commit --allow-empty -m "Trigger CI/CD"
git push origin main

# Or build locally temporarily
unset DOCKER_REGISTRY REPO_NAME IMAGE_TAG
docker-compose up --build
```

### Port Already in Use

**Solution:**
```bash
docker-compose down
# or
docker stop $(docker ps -aq)
```

### Registry Authentication Issues

**GitHub Container Registry:**
```bash
# Check if logged in
docker info | grep Username

# Re-login
docker logout ghcr.io
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

**GCP Artifact Registry:**
```bash
# Re-configure
gcloud auth configure-docker asia-east1-docker.pkg.dev
```

## 📊 Strategy Management

### Adding New Strategies

```bash
# 1. Add strategy file
cp MyStrategy.py user_data/strategies/

# 2. Update setup script
vim scripts/setup-strategies.sh
# Add "MyStrategy" to STRATEGIES array

# 3. Regenerate docker-compose.yml
bash scripts/setup-strategies.sh

# 4. Start new bot
docker-compose up -d freqtrade-mystrategy
```

### Running Backtests

```bash
# Enter bot container
docker exec -it freqtrade-trader-ichi_v1 bash

# Download data
freqtrade download-data --exchange binance \
  --pairs BTC/USDT ETH/USDT --timeframes 1h --days 30

# Run backtest
freqtrade backtesting --strategy ichiV1 \
  --timerange 20240101-20241201
```

## 🔐 Security Best Practices

### Local Development
- Use dummy credentials in env.local
- Never commit .env files
- Keep FT_UI_PASSWORD simple for local testing

### GCP Production
- Use strong passwords for FT_UI_PASSWORD
- Store secrets in GCP Secret Manager
- Use IAP tunnel instead of external IP
- Enable 2FA on GCP account
- Limit firewall rules to your IP
- Regularly update Docker images

### Registry Access
- Use Personal Access Tokens (not passwords)
- Set minimal scopes (read:packages, write:packages)
- Rotate tokens regularly
- Use separate tokens for CI/CD and manual access

## 📈 Monitoring

### View Container Logs
```bash
# All services
docker-compose logs -f

# Specific bot
docker-compose logs -f freqtrade-ichiv1

# Last 100 lines
docker-compose logs --tail=100 freqtrade-ichiv1
```

### View Trading Logs
```bash
# On GCP VM
tail -f user_data/logs/freqtrade.log

# Or via Docker
docker exec freqtrade-trader-ichi_v1 tail -f /freqtrade/user_data/logs/freqtrade.log
```

### Check Bot Status
```bash
# Via FreqUI: http://localhost:8080
# All bots should show green lights (Online status)

# Via command line
docker-compose ps
```

## 🚀 Performance Tips

### Local Development
- Use build cache: `docker-compose build --parallel`
- Prune unused images: `docker image prune -f`
- Limit logs: `docker-compose logs --tail=100`

### GCP Production
- Use appropriate VM size (e2-medium for 5 bots)
- Enable swap if needed: `sudo fallocate -l 2G /swapfile`
- Monitor memory: `docker stats`
- Clean up old images: `docker image prune -a -f`

## 📚 Additional Resources

- **Freqtrade Documentation**: https://www.freqtrade.io/
- **Docker Documentation**: https://docs.docker.com/
- **GitHub Actions**: https://docs.github.com/en/actions
- **GCP Documentation**: https://cloud.google.com/docs
- **Strategy Examples**: https://github.com/freqtrade/freqtrade-strategies

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

## ⚠️ Disclaimer

This software is for educational purposes only. Always start with dry-run mode and never risk money you cannot afford to lose. Cryptocurrency trading involves significant risk.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Need Help?**
- Check troubleshooting section above
- Join Freqtrade Discord: https://discord.gg/freqtrade
- Open an issue on GitHub
