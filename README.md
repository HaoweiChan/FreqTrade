# Freqtrade Basic Usage & GCP Deployment Guide

![Freqtrade](https://img.shields.io/badge/Freqtrade-Trading%20Bot-blue)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![GCP](https://img.shields.io/badge/GCP-Cloud%20Deploy-green)

## 🚀 Quick Start - Deploy Your Strategies to GCP

1. **Setup**: Run `scripts/setup-strategies.sh` to prepare your top 20 strategies
2. **Deploy**: Run `scripts/deploy-gcp.sh` to deploy to Google Cloud Platform  
3. **Access**: Your freqtrade bot UI at `http://EXTERNAL_IP:8080`

## 📁 Project Structure

```
freqtrade/
├── scripts/                    # 🛠️ Deployment scripts
│   ├── setup-strategies.sh     # Prepare strategy deployment
│   ├── deploy-gcp.sh          # Deploy to GCP
│   ├── startup-script.sh      # VM initialization
│   └── README.md              # Script documentation
├── user_data/                 # 📊 Your trading configuration
│   ├── config.json           # Trading settings & API keys
│   ├── strategies/           # Your 400+ strategy files
│   ├── data/                # Historical market data
│   └── logs/                # Trading logs
├── docker-compose.yml        # 🐳 Docker configuration (auto-generated)
├── DEPLOYMENT_GUIDE.md       # 📚 Detailed deployment guide
└── README.md                 # This file
```

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Local Development Setup (macOS)](#local-development-setup-macos)
  - [Python Installation](#python-installation)
  - [Freqtrade Installation](#freqtrade-installation)
  - [Local Backtesting](#local-backtesting)
  - [Local Hyperparameter Optimization](#local-hyperparameter-optimization)
- [Quick Start with Docker](#quick-start-with-docker)
- [Basic Usage](#basic-usage)
  - [Opening the Web UI](#opening-the-web-ui)
  - [Running Backtests](#running-backtests)
  - [Hyperparameter Optimization](#hyperparameter-optimization)
- [GCP Deployment](#gcp-deployment)
- [Strategy Management](#strategy-management)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

## Overview

Freqtrade is a free and open-source cryptocurrency algorithmic trading software written in Python. It supports all major exchanges, provides backtesting capabilities, and includes a web interface for monitoring and control.

**Key Features:**
- Strategy development in Python using pandas
- Historical data download and backtesting
- Hyperparameter optimization using machine learning
- Web UI and Telegram bot integration
- Support for dry-run and live trading modes
- Advanced features like FreqAI for ML-based predictions

## Prerequisites

### Local Development
- Docker & Docker Compose
- Git (for cloning strategies)
- Basic understanding of trading concepts

### GCP Deployment
- Google Cloud Platform account
- `gcloud` CLI installed and configured
- Docker registry access (Google Container Registry or Artifact Registry)
- Sufficient GCP quotas for Compute Engine

## Local Development Setup (macOS)

This section covers setting up Freqtrade with Python for local development, backtesting, and hyperopt on macOS.

### Python Installation

#### Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Install Python and Required Tools
```bash
# Install Python 3.11 (recommended for Freqtrade)
brew install python@3.11

# Install TA-Lib (required for technical analysis)
brew install ta-lib

# Install other dependencies
brew install git curl
```

#### Alternative: Using pyenv for Python Version Management
```bash
# Install pyenv
brew install pyenv

# Add to your shell profile (.zshrc for zsh)
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install and set Python 3.11
pyenv install 3.11.7
pyenv global 3.11.7
```

### Freqtrade Installation

#### Create Project Directory
```bash
mkdir ~/freqtrade-local
cd ~/freqtrade-local
```

#### Set Up Virtual Environment
```bash
# Create virtual environment
python3 -m venv freqtrade_env

# Activate virtual environment
source freqtrade_env/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### Install Freqtrade
```bash
# Install Freqtrade with all dependencies
pip install freqtrade[all]

# Alternative: Install from source for latest features
git clone https://github.com/freqtrade/freqtrade.git
cd freqtrade
pip install -e .
cd ..
```

#### Create User Directory Structure
```bash
freqtrade create-userdir --userdir user_data
```

#### Generate Configuration
```bash
freqtrade new-config --config user_data/config.json
```

### Configuration for Local Development

Edit `user_data/config.json` for local development:

```json
{
  "max_open_trades": 5,
  "stake_currency": "USDT",
  "stake_amount": 100,
  "tradable_balance_ratio": 0.99,
  "fiat_display_currency": "USD",
  "dry_run": true,
  "dry_run_wallet": 10000,
  "cancel_open_orders_on_exit": false,
  "trading_mode": "spot",
  "margin_mode": "",
  "unfilledtimeout": {
    "entry": 10,
    "exit": 10,
    "exit_timeout_count": 0,
    "unit": "minutes"
  },
  "entry_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1,
    "price_last_balance": 0.0,
    "check_depth_of_market": {
      "enabled": false,
      "bids_to_ask_delta": 1
    }
  },
  "exit_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1
  },
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": {},
    "ccxt_async_config": {},
    "pair_whitelist": [
      "BTC/USDT",
      "ETH/USDT",
      "ADA/USDT",
      "DOT/USDT"
    ],
    "pair_blacklist": []
  },
  "pairlists": [
    {
      "method": "StaticPairList"
    }
  ],
  "edge": {
    "enabled": false,
    "process_throttle_secs": 3600,
    "calculate_since_number_of_days": 7,
    "allowed_risk": 0.01,
    "stoploss_range_min": -0.01,
    "stoploss_range_max": -0.1,
    "stoploss_range_step": -0.01,
    "minimum_winrate": 0.60,
    "minimum_expectancy": 0.20,
    "min_trade_number": 10,
    "max_trade_duration_minute": 1440,
    "remove_pumps": false
  },
  "telegram": {
    "enabled": false
  },
  "api_server": {
    "enabled": true,
    "listen_ip_address": "127.0.0.1",
    "listen_port": 8080,
    "verbosity": "error",
    "enable_openapi": true,
    "jwt_secret_key": "your-local-secret-key",
    "CORS_origins": [],
    "username": "admin",
    "password": "password"
  },
  "bot_name": "freqtrade-local",
  "initial_state": "running",
  "force_entry_enable": false,
  "internals": {
    "process_throttle_secs": 5
  }
}
```

### Local Backtesting

#### Download Historical Data
```bash
# Activate virtual environment
source freqtrade_env/bin/activate

# Download data for multiple timeframes
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT ADA/USDT DOT/USDT \
  --timeframes 1m 5m 15m 1h 4h 1d \
  --days 365 \
  --config user_data/config.json
```

#### Create a Simple Test Strategy
Create `user_data/strategies/TestStrategy.py`:

```python
from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class TestStrategy(IStrategy):
    """
    Simple test strategy for local development
    """
    INTERFACE_VERSION = 3
    
    # Minimal ROI designed for the strategy
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }
    
    # Optimal stoploss
    stoploss = -0.10
    
    # Optimal timeframe
    timeframe = '5m'
    
    # Run "populate_indicators()" only for new candle
    process_only_new_candles = False
    
    # These values can be overridden in the config
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    
    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the dataframe
        """
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)
        
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        
        # Bollinger Bands
        bollinger = ta.BBANDS(dataframe)
        dataframe['bb_lowerband'] = bollinger['lowerband']
        dataframe['bb_middleband'] = bollinger['middleband']
        dataframe['bb_upperband'] = bollinger['upperband']
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        """
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) &  # RSI oversold
                (dataframe['macd'] > dataframe['macdsignal']) &  # MACD above signal
                (dataframe['close'] < dataframe['bb_lowerband']) &  # Price below lower BB
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'enter_long'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        """
        dataframe.loc[
            (
                (dataframe['rsi'] > 70) &  # RSI overbought
                (dataframe['macd'] < dataframe['macdsignal']) &  # MACD below signal
                (dataframe['close'] > dataframe['bb_upperband']) &  # Price above upper BB
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'exit_long'] = 1
        
        return dataframe
```

#### Run Local Backtests
```bash
# Basic backtest
freqtrade backtesting \
  --config user_data/config.json \
  --strategy TestStrategy \
  --timerange 20240101-20241201

# Detailed backtest with breakdown
freqtrade backtesting \
  --config user_data/config.json \
  --strategy TestStrategy \
  --timerange 20240101-20241201 \
  --breakdown day month \
  --cache none

# Backtest with specific timeframe
freqtrade backtesting \
  --config user_data/config.json \
  --strategy TestStrategy \
  --timerange 20240101-20241201 \
  --timeframe 1h

# Export detailed results
freqtrade backtesting \
  --config user_data/config.json \
  --strategy TestStrategy \
  --timerange 20240101-20241201 \
  --export trades signals \
  --export-filename user_data/backtest_results/detailed_results
```

### Local Hyperparameter Optimization

#### Create Hyperopt-Ready Strategy
Create `user_data/strategies/HyperOptStrategy.py`:

```python
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, CategoricalParameter
from pandas import DataFrame
import talib.abstract as ta
from functools import reduce


class HyperOptStrategy(IStrategy):
    """
    Strategy with hyperopt parameters for optimization
    """
    INTERFACE_VERSION = 3
    
    # Hyperopt Parameters
    buy_rsi = IntParameter(20, 40, default=30, space="buy")
    sell_rsi = IntParameter(60, 80, default=70, space="sell")
    
    buy_macd_signal = CategoricalParameter([True, False], default=True, space="buy")
    sell_macd_signal = CategoricalParameter([True, False], default=True, space="sell")
    
    roi_p1 = DecimalParameter(0.01, 0.05, default=0.02, space="roi")
    roi_p2 = DecimalParameter(0.02, 0.08, default=0.04, space="roi")
    roi_t1 = IntParameter(10, 60, default=30, space="roi")
    roi_t2 = IntParameter(30, 120, default=60, space="roi")
    
    stoploss_value = DecimalParameter(-0.20, -0.05, default=-0.10, space="stoploss")
    
    timeframe = '5m'
    startup_candle_count: int = 30
    
    @property
    def minimal_roi(self):
        return {
            "0": self.roi_p2.value,
            str(self.roi_t1.value): self.roi_p1.value,
            str(self.roi_t2.value): 0
        }
    
    @property
    def stoploss(self):
        return self.stoploss_value.value
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe)
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            dataframe['rsi'] < self.buy_rsi.value,
            dataframe['volume'] > 0
        ]
        
        if self.buy_macd_signal.value:
            conditions.append(dataframe['macd'] > dataframe['macdsignal'])
        
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'enter_long'
            ] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            dataframe['rsi'] > self.sell_rsi.value,
            dataframe['volume'] > 0
        ]
        
        if self.sell_macd_signal.value:
            conditions.append(dataframe['macd'] < dataframe['macdsignal'])
        
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'exit_long'
            ] = 1
        
        return dataframe
```

#### Run Hyperparameter Optimization
```bash
# Basic hyperopt
freqtrade hyperopt \
  --config user_data/config.json \
  --hyperopt-loss SharpeHyperOptLoss \
  --strategy HyperOptStrategy \
  --timerange 20240101-20241201 \
  --epochs 100 \
  --spaces buy sell roi stoploss

# Advanced hyperopt with more epochs
freqtrade hyperopt \
  --config user_data/config.json \
  --hyperopt-loss SortinoHyperOptLoss \
  --strategy HyperOptStrategy \
  --timerange 20240101-20241201 \
  --epochs 1000 \
  --spaces all \
  --min-trades 50 \
  --random-state 42

# Hyperopt with custom loss function
freqtrade hyperopt \
  --config user_data/config.json \
  --hyperopt-loss CalmarHyperOptLoss \
  --strategy HyperOptStrategy \
  --timerange 20240101-20241201 \
  --epochs 500 \
  --spaces buy sell \
  --hyperopt-random-state 42
```

#### View and Apply Hyperopt Results
```bash
# List hyperopt results
freqtrade hyperopt-list --best

# Show specific result details
freqtrade hyperopt-show -n 1

# Apply hyperopt results to strategy
freqtrade hyperopt-show -n 1 --print-json > user_data/hyperopt_results/best_params.json
```

### Data Management Between Local and GCP

#### Export Local Data for GCP
```bash
# Create data archive for GCP deployment
tar -czf freqtrade-data-$(date +%Y%m%d).tar.gz user_data/

# Upload to GCS (if gcloud configured)
gsutil cp freqtrade-data-$(date +%Y%m%d).tar.gz gs://your-project-freqtrade-data/local-exports/
```

#### Sync Strategies to GCP
```bash
# Upload strategies to GCS
gsutil -m rsync -r -d user_data/strategies/ gs://your-project-freqtrade-data/strategies/

# Or use git repository for strategy management
git init user_data/strategies/
git add .
git commit -m "Initial strategies"
git remote add origin https://github.com/your-username/freqtrade-strategies.git
git push -u origin main
```

#### Local Development Commands Summary
```bash
# Daily workflow
source freqtrade_env/bin/activate

# Download latest data
freqtrade download-data --exchange binance --pairs BTC/USDT ETH/USDT --timeframes 5m 1h --days 7

# Test strategy
freqtrade backtesting --strategy YourStrategy --timerange 20241201-

# Optimize strategy
freqtrade hyperopt --strategy YourStrategy --epochs 100 --spaces buy sell

# Start local UI for analysis
freqtrade trade --strategy YourStrategy --dry-run

# Open FreqUI without trading (analysis only)
freqtrade webserver --config user_data/config.json
```

#### Opening FreqUI for Local Development
```bash
# Quick start FreqUI with your config
source freqtrade_env/bin/activate
freqtrade trade --config user_data/config.json --dry-run

# Then open browser to: http://localhost:8080
# Username/password as configured in your config.json
```

### Recommended Workflow: Local Development + GCP Production

#### 1. Local Strategy Development
```bash
# On your macOS machine
cd ~/freqtrade-local
source freqtrade_env/bin/activate

# Download fresh data
freqtrade download-data --exchange binance --pairs BTC/USDT ETH/USDT --timeframes 5m 1h --days 30

# Develop and test strategy
freqtrade backtesting --strategy MyNewStrategy --timerange 20240101-

# Optimize parameters
freqtrade hyperopt --strategy MyNewStrategy --epochs 300 --spaces all
```

#### 2. Strategy Validation
```bash
# Comprehensive backtesting
freqtrade backtesting \
  --strategy MyNewStrategy \
  --timerange 20240101-20241201 \
  --breakdown month \
  --export trades signals

# Analyze results in FreqUI
freqtrade trade --strategy MyNewStrategy --dry-run &
# Open http://localhost:8080 in browser
```

#### 3. Deploy to GCP
```bash
# Push strategies to git repository
cd user_data/strategies
git add MyNewStrategy.py
git commit -m "Add optimized MyNewStrategy"
git push origin main

# Or upload directly to GCS
gsutil cp MyNewStrategy.py gs://your-project-freqtrade-data/strategies/

# Update GCP deployment (covered in GCP section)
```

## Quick Start with Docker

### 1. Create Project Directory
```bash
mkdir freqtrade-project
cd freqtrade-project
```

### 2. Download Docker Compose File
```bash
curl https://raw.githubusercontent.com/freqtrade/freqtrade/stable/docker-compose.yml -o docker-compose.yml
```

### 3. Pull Freqtrade Image
```bash
docker compose pull
```

### 4. Create User Directory Structure
```bash
docker compose run --rm freqtrade create-userdir --userdir user_data
```

### 5. Generate Configuration
```bash
docker compose run --rm freqtrade new-config --config user_data/config.json
```

## Basic Usage

### Opening the Web UI

#### Enable FreqUI in Configuration
Edit `user_data/config.json` and ensure the following section is present:

```json
{
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "verbosity": "error",
    "enable_openapi": true,
    "jwt_secret_key": "your-secret-key-here",
    "CORS_origins": [],
    "username": "your-username",
    "password": "your-password"
  }
}
```

#### Start Freqtrade with UI
```bash
docker compose up -d
```

#### Access the Web Interface
Open your browser and navigate to:
- Local: `http://localhost:8080`
- Remote server: `http://your-server-ip:8080`

**Security Note:** For production deployments, always use HTTPS and proper authentication.

### Opening FreqUI Directly

#### Local Python Installation (macOS)
```bash
# Activate your virtual environment
source freqtrade_env/bin/activate

# Start FreqUI with your config (dry-run mode)
freqtrade trade --config user_data/config.json --strategy YourStrategy --dry-run

# Or start without specifying strategy (uses config default)
freqtrade trade --config user_data/config.json --dry-run

# Start FreqUI for analysis only (no trading)
freqtrade webserver --config user_data/config.json
```

#### Docker Installation
```bash
# Start FreqUI with Docker
docker compose run --rm -p 8080:8080 freqtrade trade --config user_data/config.json --strategy YourStrategy --dry-run

# Or start webserver only for analysis
docker compose run --rm -p 8080:8080 freqtrade webserver --config user_data/config.json
```

#### Quick Commands Summary
```bash
# For local Python development
freqtrade trade --config user_data/config.json --dry-run

# For Docker
docker compose up -d

# Access UI at: http://localhost:8080
```

### Running Backtests

#### Download Historical Data
```bash
# Download 30 days of data for specific pairs
docker compose run --rm freqtrade download-data \
  --pairs BTC/USDT ETH/USDT \
  --exchange binance \
  --days 30 \
  --timeframes 5m 1h 4h
```

#### Run Backtest
```bash
# Basic backtest with SampleStrategy
docker compose run --rm freqtrade backtesting \
  --config user_data/config.json \
  --strategy SampleStrategy \
  --timerange 20231201-20240101 \
  --timeframe 5m
```

#### Advanced Backtest with Custom Strategy
```bash
docker compose run --rm freqtrade backtesting \
  --config user_data/config.json \
  --strategy YourCustomStrategy \
  --timerange 20231201-20240101 \
  --timeframe 5m \
  --enable-position-stacking \
  --max-open-trades 5
```

### Hyperparameter Optimization

#### Basic Hyperopt
```bash
docker compose run --rm freqtrade hyperopt \
  --config user_data/config.json \
  --hyperopt-loss SharpeHyperOptLoss \
  --strategy SampleStrategy \
  --timerange 20231201-20240101 \
  --epochs 100 \
  --spaces buy sell roi stoploss
```

#### Advanced Hyperopt with Custom Loss Function
```bash
docker compose run --rm freqtrade hyperopt \
  --config user_data/config.json \
  --hyperopt-loss SortinoHyperOptLoss \
  --strategy YourCustomStrategy \
  --timerange 20231201-20240101 \
  --epochs 500 \
  --spaces all \
  --min-trades 100
```

#### View Hyperopt Results
```bash
# List all hyperopt results
docker compose run --rm freqtrade hyperopt-list

# Show best results
docker compose run --rm freqtrade hyperopt-list --best --no-details

# Export results to JSON
docker compose run --rm freqtrade hyperopt-list --export-csv user_data/hyperopt_results.csv
```

## GCP Deployment

### Architecture Overview

The GCP deployment follows production best practices:
- **Compute Engine VM** with Docker for running Freqtrade
- **Cloud Storage** for persistent data and strategy backups
- **Cloud Logging** for centralized log management
- **Cloud Monitoring** for performance metrics
- **VPC & Firewall Rules** for network security
- **Cloud DNS** for custom domain (optional)

### Step 1: Prepare GCP Environment

#### Set Up Project and Authentication
```bash
# Set your project ID
export PROJECT_ID="your-freqtrade-project"
export REGION="us-central1"
export ZONE="us-central1-a"

# Set default project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
```

### Step 2: Create Infrastructure

#### Create VPC Network
```bash
# Create custom VPC
gcloud compute networks create freqtrade-network --subnet-mode custom

# Create subnet
gcloud compute networks subnets create freqtrade-subnet \
  --network freqtrade-network \
  --range 10.1.0.0/24 \
  --region $REGION
```

#### Create Firewall Rules
```bash
# Allow SSH access
gcloud compute firewall-rules create freqtrade-allow-ssh \
  --network freqtrade-network \
  --allow tcp:22 \
  --source-ranges 0.0.0.0/0 \
  --target-tags freqtrade-vm

# Allow HTTP/HTTPS for UI (restrict source-ranges in production)
gcloud compute firewall-rules create freqtrade-allow-web \
  --network freqtrade-network \
  --allow tcp:8080,tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --target-tags freqtrade-vm
```

#### Create Cloud Storage Bucket
```bash
# Create bucket for persistent storage
gsutil mb gs://$PROJECT_ID-freqtrade-data

# Enable versioning
gsutil versioning set on gs://$PROJECT_ID-freqtrade-data
```

### Step 3: Deploy VM Instance

#### Create VM with Docker
```bash
gcloud compute instances create freqtrade-vm \
  --zone $ZONE \
  --machine-type e2-standard-2 \
  --network-interface subnet=freqtrade-subnet,network-tier=PREMIUM \
  --maintenance-policy MIGRATE \
  --provisioning-model STANDARD \
  --tags freqtrade-vm \
  --image-family ubuntu-2204-lts \
  --image-project ubuntu-os-cloud \
  --boot-disk-size 50GB \
  --boot-disk-type pd-standard \
  --metadata-from-file startup-script=scripts/startup-script.sh
```

#### Create Startup Script
Create `startup-script.sh`:

```bash
#!/bin/bash

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker $(whoami)

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Create freqtrade directory
mkdir -p /opt/freqtrade
cd /opt/freqtrade

# Download docker-compose file
curl https://raw.githubusercontent.com/freqtrade/freqtrade/stable/docker-compose.yml -o docker-compose.yml

# Create systemd service for freqtrade
cat > /etc/systemd/system/freqtrade.service << EOF
[Unit]
Description=Freqtrade Trading Bot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/freqtrade
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl enable freqtrade.service
```

### Step 4: Configure Persistent Storage

#### Create Docker Compose with GCS Sync
Create `docker-compose.yml` for production:

```yaml
version: '3.8'

services:
  freqtrade:
    image: freqtradeorg/freqtrade:stable
    restart: unless-stopped
    container_name: freqtrade
    volumes:
      - "./user_data:/freqtrade/user_data"
    ports:
      - "8080:8080"
    command: >
      trade
      --logfile /freqtrade/user_data/logs/freqtrade.log
      --db-url sqlite:////freqtrade/user_data/tradesv3.sqlite
      --config /freqtrade/user_data/config.json
      --strategy-path /freqtrade/user_data/strategies

  backup:
    image: google/cloud-sdk:alpine
    restart: "no"
    volumes:
      - "./user_data:/data"
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/data/gcp-key.json
    command: >
      sh -c "
        gcloud auth activate-service-account --key-file=/data/gcp-key.json &&
        gsutil -m rsync -r -d /data gs://${PROJECT_ID}-freqtrade-data/backup/
      "
```

#### Set Up Automated Backups
Create backup script `backup.sh`:

```bash
#!/bin/bash

PROJECT_ID="your-freqtrade-project"
BACKUP_BUCKET="gs://$PROJECT_ID-freqtrade-data"

# Stop freqtrade for consistent backup
docker-compose stop freqtrade

# Sync data to GCS
gsutil -m rsync -r -d /opt/freqtrade/user_data $BACKUP_BUCKET/backup/$(date +%Y%m%d_%H%M%S)/

# Restart freqtrade
docker-compose start freqtrade

# Clean old backups (keep last 7 days)
gsutil -m rm -r $(gsutil ls $BACKUP_BUCKET/backup/ | head -n -7)
```

Add to crontab for daily backups:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/freqtrade/backup.sh
```

### Step 5: Security Hardening

#### Create Service Account with Minimal Permissions
```bash
# Create service account
gcloud iam service-accounts create freqtrade-sa \
  --display-name "Freqtrade Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:freqtrade-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role roles/storage.objectAdmin

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:freqtrade-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role roles/logging.logWriter

# Create and download key
gcloud iam service-accounts keys create /opt/freqtrade/user_data/gcp-key.json \
  --iam-account freqtrade-sa@$PROJECT_ID.iam.gserviceaccount.com
```

#### Configure SSL/TLS (Optional)
For production with custom domain:

```bash
# Install certbot
apt-get install certbot nginx -y

# Configure nginx reverse proxy
cat > /etc/nginx/sites-available/freqtrade << EOF
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site and get SSL certificate
ln -s /etc/nginx/sites-available/freqtrade /etc/nginx/sites-enabled/
certbot --nginx -d your-domain.com
```

## Strategy Management

### Adding Custom Strategies

#### Copy Strategies to VM
```bash
# Copy from local machine
scp -r ./user_data/strategies/* user@vm-ip:/opt/freqtrade/user_data/strategies/

# Or clone from repository
git clone https://github.com/your-username/freqtrade-strategies.git /opt/freqtrade/user_data/strategies/
```

#### Validate Strategy
```bash
docker compose run --rm freqtrade list-strategies
docker compose run --rm freqtrade test-pairlist -c user_data/config.json
```

### FreqAI Integration

For ML-based strategies, use the FreqAI-enabled image:

```yaml
services:
  freqtrade:
    image: freqtradeorg/freqtrade:stable_freqai
    # ... rest of configuration
```

## Monitoring & Logging

### Cloud Logging Integration

#### Configure Logging Agent
```bash
# Install Ops Agent
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# Configure log collection
cat > /etc/google-cloud-ops-agent/config.yaml << EOF
logging:
  receivers:
    freqtrade_logs:
      type: files
      include_paths:
        - /opt/freqtrade/user_data/logs/*.log
  service:
    pipelines:
      default_pipeline:
        receivers: [freqtrade_logs]
EOF

systemctl restart google-cloud-ops-agent
```

### Monitoring Setup

#### Create Monitoring Dashboard
```bash
# Create custom metrics (example)
gcloud logging metrics create freqtrade_trades \
  --description="Number of trades executed" \
  --log-filter='resource.type="gce_instance" AND jsonPayload.message:"Trade opened"'
```

## Troubleshooting

### Common Issues

#### VM Instance Issues
```bash
# Check VM status
gcloud compute instances describe freqtrade-vm --zone $ZONE

# SSH into VM
gcloud compute ssh freqtrade-vm --zone $ZONE

# Check logs
sudo journalctl -u freqtrade.service -f
```

#### Docker Issues
```bash
# Check container status
docker compose ps

# View container logs
docker compose logs freqtrade

# Restart services
docker compose restart
```

#### Storage Issues
```bash
# Check disk usage
df -h

# Check GCS sync
gsutil ls gs://$PROJECT_ID-freqtrade-data/backup/
```

#### Network Issues
```bash
# Test API connectivity
curl -s https://api.binance.com/api/v3/ping

# Check firewall rules
gcloud compute firewall-rules list --filter="network:freqtrade-network"
```

### Performance Optimization

#### VM Sizing Recommendations
- **Development/Testing**: e2-micro (1 vCPU, 1GB RAM)
- **Single Strategy**: e2-standard-2 (2 vCPUs, 8GB RAM)
- **Multiple Strategies/FreqAI**: c2-standard-4 (4 vCPUs, 16GB RAM)

#### Cost Optimization
- Use preemptible instances for development
- Implement auto-shutdown during market close
- Use committed use discounts for production

### Local Development Troubleshooting (macOS)

#### TA-Lib Installation Issues
```bash
# If TA-Lib installation fails
brew install ta-lib

# Alternative: Install from source
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr/local
make
sudo make install

# Then install Python wrapper
pip install TA-Lib
```

#### Python Version Issues
```bash
# Check Python version
python3 --version

# If using pyenv, ensure correct version
pyenv versions
pyenv local 3.11.7
```

#### Virtual Environment Issues
```bash
# If activation fails
deactivate  # if already in a venv
rm -rf freqtrade_env
python3 -m venv freqtrade_env
source freqtrade_env/bin/activate
pip install --upgrade pip
pip install freqtrade[all]
```

#### Memory Issues During Hyperopt
```bash
# Reduce epochs or limit pairs
freqtrade hyperopt --epochs 50 --min-trades 20

# Or increase virtual memory
sudo sysctl -w vm.max_map_count=262144
```

#### Data Download Issues
```bash
# Clear cache and retry
rm -rf user_data/data/.cache
freqtrade download-data --exchange binance --pairs BTC/USDT --days 7 --timeframes 5m
```

### Support Resources

- **Official Documentation**: https://www.freqtrade.io/
- **Discord Community**: https://discord.gg/freqtrade
- **GitHub Issues**: https://github.com/freqtrade/freqtrade/issues
- **Strategy Repository**: https://github.com/freqtrade/freqtrade-strategies

---

**Disclaimer**: This software is for educational purposes only. Always start with dry-run mode and never risk money you cannot afford to lose. Cryptocurrency trading involves significant risk. 

## Accessing the Web UI Securely with IAP

To avoid exposing your Freqtrade instance to the public internet and to save on external IP costs, this deployment uses GCP's Identity-Aware Proxy (IAP) to create a secure tunnel.

### How to Connect:

1.  **Open a New Terminal**: After your deployment completes, open a new terminal window on your local machine.

2.  **Start the IAP Tunnel**: Run the command provided at the end of the deployment script. It will look like this:

    ```bash
    gcloud compute start-iap-tunnel freqtrade-bot 8080 --zone=asia-east1-b --local-host-port=localhost:8080 --project=oceanic-glazing-466419-v3
    ```

    This command creates a secure, encrypted tunnel from your local machine's port `8080` to the Freqtrade container running on the GCP VM.

3.  **Access the UI**: Once the tunnel is active, open your web browser and go to:

    **`http://localhost:8080`**

    You will be able to access the Freqtrade UI as if it were running locally.

4.  **Stopping the Tunnel**: To close the connection, simply go back to the terminal where the tunnel is running and press `Ctrl+C`.

This method is highly recommended as it enhances security and is more cost-effective. 