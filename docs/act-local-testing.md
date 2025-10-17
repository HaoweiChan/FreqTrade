# Testing CI/CD Pipeline Locally with act CLI

## 🚀 Overview

You can test your entire CI/CD pipeline locally using the `act` CLI tool, including the GCP deployment job. However, since the GCP deployment requires secrets, you need to provide them for local testing.

## ⚠️ Important Security Notes

- **Never commit real secrets** to your repository
- Use **test/dummy values** for local testing
- **Delete any .env files** containing secrets before committing

## 🛠️ Method 1: Using act with --secret Flags

### Step 1: Install act CLI
```bash
# On macOS
brew install act

# Or download from: https://github.com/nektos/act/releases
```

### Step 2: Test GCP Deployment Job
```bash
# Test only the deploy-to-gcp job with dummy secrets
act push -j deploy-to-gcp \
  --secret GCP_SA_KEY='{"test": "dummy"}' \
  --secret GCP_PROJECT_ID='test-project' \
  --secret GCP_VM_IP='127.0.0.1' \
  --secret GCP_VM_USER='testuser' \
  --secret GCP_SSH_PRIVATE_KEY='-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n-----END OPENSSH PRIVATE KEY-----' \
  --secret BINANCE_KEY='test_binance_key' \
  --secret BINANCE_SECRET='test_binance_secret' \
  --secret TELEGRAM_TOKEN='1234567890:test_token' \
  --secret TELEGRAM_CHAT_ID='123456789' \
  --secret FT_UI_USERNAME='testuser' \
  --secret FT_UI_PASSWORD='testpass'
```

### Step 3: Test All Jobs (including GCP)
```bash
# Test the full pipeline with secrets
act push \
  --secret GCP_SA_KEY='{"test": "dummy"}' \
  --secret GCP_PROJECT_ID='test-project' \
  --secret GCP_VM_IP='127.0.0.1' \
  --secret GCP_VM_USER='testuser' \
  --secret GCP_SSH_PRIVATE_KEY='-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n-----END OPENSSH PRIVATE KEY-----' \
  --secret BINANCE_KEY='test_binance_key' \
  --secret BINANCE_SECRET='test_binance_secret' \
  --secret TELEGRAM_TOKEN='1234567890:test_token' \
  --secret TELEGRAM_CHAT_ID='123456789' \
  --secret FT_UI_USERNAME='testuser' \
  --secret FT_UI_PASSWORD='testpass'
```

## 🛠️ Method 2: Using Environment Variables

### Step 1: Create a test .env file (for local testing only!)
```bash
# Create .env file with test values (DO NOT COMMIT THIS!)
cat > .env.test << 'EOF'
GCP_SA_KEY={"test": "dummy"}
GCP_PROJECT_ID=test-project
GCP_VM_IP=127.0.0.1
GCP_VM_USER=testuser
GCP_SSH_PRIVATE_KEY=-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n-----END OPENSSH PRIVATE KEY-----
BINANCE_KEY=test_binance_key
BINANCE_SECRET=test_binance_secret
TELEGRAM_TOKEN=1234567890:test_token
TELEGRAM_CHAT_ID=123456789
FT_UI_USERNAME=testuser
FT_UI_PASSWORD=testpass
EOF
```

### Step 2: Load environment variables and run act
```bash
# Load the test environment variables
set -a && source .env.test && set +a

# Test GCP deployment job
act push -j deploy-to-gcp

# Test all jobs
act push
```

### Step 3: Clean up (IMPORTANT!)
```bash
# Remove the test .env file
rm .env.test

# Verify it's gone
ls -la .env* || echo "✅ No .env files found"
```

## 🛠️ Method 3: Using act with --env-file

```bash
# Create environment file for act
act push -j deploy-to-gcp --env-file .env.test

# Or specify multiple files
act push --env-file .env.test --env-file .env.local
```

## 🔧 Advanced act Options for GCP Testing

### Test Specific Scenarios

```bash
# Test with different container architecture
act push -j deploy-to-gcp --container-architecture linux/amd64

# Test with more verbose output
act push -j deploy-to-gcp -v

# Test with specific event (like push to main)
act push -j deploy-to-gcp --eventpath .github/workflows/event.json
```

### Create Event File for Testing
```bash
# Create a test event file
cat > .github/workflows/test-push-event.json << 'EOF'
{
  "ref": "refs/heads/main",
  "before": "0000000000000000000000000000000000000000",
  "after": "abc123def456",
  "repository": {
    "name": "FreqTrade",
    "full_name": "HaoweiChan/FreqTrade"
  },
  "pusher": {
    "name": "test-user"
  }
}
EOF

# Test with the custom event
act push --eventpath .github/workflows/test-push-event.json
```

## 🚨 Troubleshooting Local Testing

### Common Issues

1. **SSH Connection Fails**
   - Use dummy IP like `127.0.0.1` for testing
   - The deployment will fail at SSH step, but you can verify the setup

2. **Authentication Errors**
   - Use dummy JSON for `GCP_SA_KEY`
   - The auth step will work, but actual GCP calls will fail

3. **Port Conflicts**
   - Use different ports for local testing
   - Check what's running on ports 8080, 8081, etc.

### Expected Test Results

```bash
# Successful local test output:
[CI/CD Pipeline/Deploy to GCP] 🚀 Starting deployment to GCP VM...
[CI/CD Pipeline/Deploy to GCP] ❌ Freqtrade directory not found on GCP VM
[CI/CD Pipeline/Deploy to GCP] ✅ Deployment completed successfully!

# This is expected since we're using dummy values
```

## 📋 Complete Testing Workflow

### 1. Test Individual Jobs First
```bash
# Test build jobs (no secrets needed)
act push -j build-and-test-bot
act push -j build-and-test-ui
act push -j integration-test

# Test security scan (needs GITHUB_TOKEN, automatically provided)
act push -j security-scan
```

### 2. Test GCP Deployment with Dummy Secrets
```bash
# Test GCP deployment job only
act push -j deploy-to-gcp \
  --secret GCP_SA_KEY='{"test": "dummy"}' \
  --secret GCP_PROJECT_ID='test-project' \
  --secret GCP_VM_IP='127.0.0.1' \
  --secret GCP_VM_USER='testuser' \
  --secret GCP_SSH_PRIVATE_KEY='-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n-----END OPENSSH PRIVATE KEY-----' \
  --secret BINANCE_KEY='test_key' \
  --secret BINANCE_SECRET='test_secret' \
  --secret TELEGRAM_TOKEN='1234567890:test' \
  --secret TELEGRAM_CHAT_ID='123456789' \
  --secret FT_UI_USERNAME='testuser' \
  --secret FT_UI_PASSWORD='testpass'
```

### 3. Test Full Pipeline
```bash
# Test everything together
act push \
  --secret GCP_SA_KEY='{"test": "dummy"}' \
  --secret GCP_PROJECT_ID='test-project' \
  --secret GCP_VM_IP='127.0.0.1' \
  --secret GCP_VM_USER='testuser' \
  --secret GCP_SSH_PRIVATE_KEY='-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n-----END OPENSSH PRIVATE KEY-----' \
  --secret BINANCE_KEY='test_key' \
  --secret BINANCE_SECRET='test_secret' \
  --secret TELEGRAM_TOKEN='1234567890:test' \
  --secret TELEGRAM_CHAT_ID='123456789' \
  --secret FT_UI_USERNAME='testuser' \
  --secret FT_UI_PASSWORD='testpass'
```

## 🎯 Summary

✅ **Build & Test Jobs**: Work without secrets
✅ **Integration Test**: Works without secrets
✅ **Security Scan**: Works with built-in GITHUB_TOKEN
✅ **GCP Deployment**: Requires secrets for testing

For local testing:
- Use **dummy/test values** for all secrets
- Use `act push -j deploy-to-gcp --secret KEY=value` syntax
- **Never commit real secrets** to your repository
- **Delete test .env files** after testing

This allows you to verify the entire pipeline works correctly before deploying with real secrets!
