# Per-Bot Trading Mode Configuration

This document explains how to control dry-run vs live trading mode for individual bots.

## Overview

Each bot can be independently set to either **dry-run mode** (paper trading) or **live trading mode** (real money). This is controlled via environment variables in your `.env` file.

## Configuration

### Environment Variables

Add these to your `.env` file on the GCP VM:

```bash
# Per-Bot Dry-Run Control
# Set to "false" to enable live trading for specific bots
# Default: true (dry-run mode for safety)

ICHI_DRY_RUN=true
LOOKAHEAD_DRY_RUN=true
MACD_DRY_RUN=true
PSAR_DRY_RUN=true
MACDCCI_DRY_RUN=true
```

### Container Names

Each container name now includes the mode indicator:
- `freqtrade-trader-ichi_v1-DRYRUN` (dry-run mode)
- `freqtrade-trader-macd-LIVE` (live trading mode)

## How to Enable Live Trading

### Option 1: Via .env File (Recommended)

1. **SSH into your GCP VM:**
   ```bash
   ssh user@your-vm-ip
   cd ~/freqtrade
   ```

2. **Edit the .env file:**
   ```bash
   nano .env
   ```

3. **Change the desired bot to live mode:**
   ```bash
   # Enable live trading for MACD bot only
   MACD_DRY_RUN=false
   
   # All other bots remain in dry-run
   ICHI_DRY_RUN=true
   LOOKAHEAD_DRY_RUN=true
   PSAR_DRY_RUN=true
   MACDCCI_DRY_RUN=true
   ```

4. **Update container name (manual step):**
   ```bash
   # Edit docker-compose.yml
   # Change: container_name: freqtrade-trader-macd-DRYRUN
   # To:     container_name: freqtrade-trader-macd-LIVE
   ```

5. **Restart the specific bot:**
   ```bash
   docker compose up -d --force-recreate freqtrade-macd
   ```

### Option 2: Via GitHub Secrets (CI/CD)

1. **Add secrets to GitHub repository:**
   - Go to Settings → Secrets and variables → Actions
   - Add: `MACD_DRY_RUN` with value `false`

2. **Update `.github/workflows/ci-cd.yml`:**
   ```yaml
   env:
     MACD_DRY_RUN: ${{ secrets.MACD_DRY_RUN || 'true' }}
   ```

3. **Push changes and deploy via CI/CD**

## Safety Checks

### Before Enabling Live Trading:

1. ✅ **Test thoroughly in dry-run mode** (at least 1-2 weeks)
2. ✅ **Verify strategy profitability** with sufficient data
3. ✅ **Set appropriate risk limits:**
   - Max stake amount
   - Max open trades
   - Stop loss percentage
4. ✅ **Enable Telegram notifications** to monitor trades
5. ✅ **Start with small stake amounts**
6. ✅ **Monitor closely** for the first 24-48 hours

### Verification After Switch:

```bash
# Check if bot is in live mode
docker logs freqtrade-trader-macd | grep "Dry run"
# Should show: "Dry run is disabled"

# Check container name
docker ps | grep freqtrade
# Should show: freqtrade-trader-macd-LIVE
```

## Example Scenarios

### Scenario 1: Test New Strategy
```bash
# Keep new strategy in dry-run
LOOKAHEAD_DRY_RUN=true

# Other proven strategies in live mode
MACD_DRY_RUN=false
ICHI_DRY_RUN=false
```

### Scenario 2: Gradual Rollout
```bash
# Week 1: Only MACD live
MACD_DRY_RUN=false
ICHI_DRY_RUN=true
PSAR_DRY_RUN=true

# Week 2: Add ICHI if MACD performs well
MACD_DRY_RUN=false
ICHI_DRY_RUN=false
PSAR_DRY_RUN=true

# Week 3: Add PSAR if both perform well
MACD_DRY_RUN=false
ICHI_DRY_RUN=false
PSAR_DRY_RUN=false
```

### Scenario 3: All Dry-Run (Default/Safe)
```bash
# Keep everything in dry-run for testing
ICHI_DRY_RUN=true
LOOKAHEAD_DRY_RUN=true
MACD_DRY_RUN=true
PSAR_DRY_RUN=true
MACDCCI_DRY_RUN=true
```

## Rollback to Dry-Run

If you need to quickly disable live trading:

```bash
# SSH into VM
cd ~/freqtrade

# Edit .env and set to true
echo "MACD_DRY_RUN=true" >> .env

# Restart the bot
docker compose up -d --force-recreate freqtrade-macd

# Verify
docker logs freqtrade-trader-macd | grep "Dry run"
# Should show: "Dry run is enabled"
```

## Important Notes

1. **Separate Databases**: Each bot uses the shared `user_data/tradesv3.sqlite` database. Consider using separate config files if you need isolated data.

2. **Restart Required**: Changes to dry-run mode require a container restart to take effect.

3. **No UI Toggle**: There is intentionally NO switch in FreqUI to toggle modes - this prevents accidental live trading.

4. **Container Names**: Update container names manually in `docker-compose.yml` to reflect the mode (DRYRUN vs LIVE) for clarity.

5. **Monitoring**: Always monitor live trading bots closely, especially in the first few days after switching modes.

