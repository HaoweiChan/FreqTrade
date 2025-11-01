# GCP Deployment Secrets Setup - Step by Step Guide

The CI/CD pipeline will **automatically skip** GCP deployment if these secrets are not configured. To enable GCP deployment, add the following secrets to your GitHub repository.

## Required GitHub Secrets

Go to: **GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**

## 📋 Complete Step-by-Step Instructions

### 1. GCP Authentication Secrets

#### **GCP_SA_KEY** - Service Account Key (JSON)
1. **Open GCP Console**: https://console.cloud.google.com/
2. **Navigate**: IAM & Admin → Service Accounts
3. **Create Service Account** (if you don't have one):
   - Click "Create Service Account"
   - Name: `freqtrade-deployer`
   - Description: "For Freqtrade CI/CD deployment"
   - Click "Create and Continue"
4. **Grant Permissions**:
   - Role: `Compute Instance Admin (v1)`
   - Click "Done"
5. **Create Key**:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Format: `JSON`
   - Click "Create"
   - **Copy the entire JSON content** - this is your `GCP_SA_KEY`

#### **GCP_PROJECT_ID** - Your Project ID
1. **GCP Console**: https://console.cloud.google.com/
2. **Top left**: Click project dropdown
3. **Copy the Project ID** (not the project name)
   ```
   Example: my-freqtrade-project-123456
   ```

### 2. GCP VM Access Secrets

**Option A: Using gcloud compute ssh (RECOMMENDED - Works without external IP)**

This method uses GCP's Identity-Aware Proxy (IAP) and works even if your VM doesn't have an external IP address.

#### **GCP_VM_INSTANCE** - VM Instance Name
1. **GCP Console**: Compute Engine → VM instances
2. **Find your VM instance**
3. **Copy the instance name** (first column)
   ```
   Example: freqtrade-bot
   ```

#### **GCP_VM_ZONE** - VM Zone
1. **GCP Console**: Compute Engine → VM instances
2. **Click your VM instance**
3. **Copy the Zone** from instance details
   ```
   Example: asia-east1-b
   ```

#### **GCP_VM_USER** - SSH Username
1. **GCP Console**: Compute Engine → VM instances
2. **Click your VM instance**
3. **Copy the username** (usually your email prefix)
   ```
   Example: freqtrade_user
   ```

**Option B: Using Direct SSH (Requires External IP)**

If you prefer direct SSH access, you'll need:

#### **GCP_VM_IP** - VM External IP
1. **GCP Console**: Compute Engine → VM instances
2. **Click your VM instance**
3. **Copy "External IP"** from the instance details
   ```
   Example: 34.123.45.67
   ```

#### **GCP_SSH_PRIVATE_KEY** - SSH Private Key
1. **Generate SSH Key Pair** (on your local machine):
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```
   - Press Enter for default location (`~/.ssh/id_rsa`)
   - Set a passphrase (or leave empty)

2. **Add Public Key to GCP VM**:
   - **GCP Console**: Compute Engine → VM instances → [Your VM]
   - Click "Edit"
   - Scroll to "SSH Keys"
   - Click "Show and edit"
   - Click "+ Add item"
   - **Paste your public key** (`cat ~/.ssh/id_rsa.pub`)
   - Click "Save"

3. **Get Private Key Content**:
   ```bash
   cat ~/.ssh/id_rsa
   ```
   - **Copy the entire output** - this is your `GCP_SSH_PRIVATE_KEY`
   - It starts with `-----BEGIN OPENSSH PRIVATE KEY-----`

### 3. Trading Bot Configuration Secrets

#### **BINANCE_KEY** & **BINANCE_SECRET**
1. **Binance Account**: https://www.binance.com/en/my/settings/api-management
2. **Create API Key**:
   - Click "Create API Key"
   - Label: "Freqtrade Trading"
   - Enable: Spot & Margin Trading
   - Click "Create"
   - **Copy API Key** → `BINANCE_KEY`
   - **Copy Secret Key** → `BINANCE_SECRET`

#### **TELEGRAM_TOKEN** & **TELEGRAM_CHAT_ID**
1. **Create Telegram Bot**:
   - Message @BotFather on Telegram
   - Send: `/newbot`
   - Follow instructions to name your bot
   - **Copy the Token** → `TELEGRAM_TOKEN`

2. **Get Your Chat ID**:
   - Message @userinfobot on Telegram
   - **Copy your Chat ID** → `TELEGRAM_CHAT_ID`

#### **FT_UI_USERNAME** & **FT_UI_PASSWORD**
1. **Choose credentials for FreqUI access**
   - These can be any values you want
   - **Remember them** for accessing the web interface

## 🚀 Deployment Flow

Once secrets are configured:
1. Push to `main` branch triggers the pipeline
2. All tests run (bot, UI, integration, security)
3. If secrets are available, deployment to GCP starts automatically
4. The deployment script pulls latest images from GitHub Container Registry
5. Services restart on the GCP VM

## ✅ Testing Without GCP

The pipeline will work perfectly fine without GCP secrets configured:
- ✅ Build bot image
- ✅ Build UI image
- ✅ Run integration tests
- ✅ Security scan
- ⏭️  Skip GCP deployment (no secrets)

All checks will pass! 🚀

## 🔧 Quick Setup Commands

```bash
# After getting all values, add them to GitHub secrets:
# Go to GitHub → Settings → Secrets and variables → Actions
# Create each secret with the values you copied above
```

## 📝 Example Secret Values

```
GCP_SA_KEY: {"type":"service_account","project_id":"my-project-123","private_key_id":"abc123",...}
GCP_PROJECT_ID: my-freqtrade-project-123
GCP_VM_IP: 34.123.45.67
GCP_VM_USER: freqtrade_user
GCP_SSH_PRIVATE_KEY: -----BEGIN OPENSSH PRIVATE KEY-----\nabc123...\n-----END OPENSSH PRIVATE KEY-----
BINANCE_KEY: your_binance_api_key
BINANCE_SECRET: your_binance_secret
TELEGRAM_TOKEN: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID: 123456789
FT_UI_USERNAME: admin
FT_UI_PASSWORD: your_secure_password
```

