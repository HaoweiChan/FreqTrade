# SSH Key Setup Guide for GCP VM Access

## Do You Need a New SSH Key?

**Only if:**
1. You don't have an SSH key pair generated yet
2. Your existing SSH key was lost or compromised
3. The SSH key you're using doesn't have access to the GCP VM

**If your SSH key worked before (commit 5fa0f3b), you probably DON'T need a new one.**

## How to Generate a New SSH Key Pair

### Step 1: Generate SSH Key Pair

On your local machine, run:

```bash
# Generate a new SSH key pair (4096-bit RSA)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/gcp_freqtrade_key

# When prompted:
# - Press Enter for passphrase (or set one for extra security)
# - Press Enter again to confirm
```

This creates two files:
- `~/.ssh/gcp_freqtrade_key` (private key - KEEP SECRET!)
- `~/.ssh/gcp_freqtrade_key.pub` (public key - safe to share)

### Step 2: Add Public Key to GCP VM

#### Option A: Via GCP Console (Recommended)

1. **Open GCP Console**: https://console.cloud.google.com/
2. **Navigate**: Compute Engine → VM instances
3. **Click your VM instance**
4. **Click "Edit"** button
5. **Scroll down** to "SSH Keys" section
6. **Click "Show and edit"**
7. **Click "+ Add item"**
8. **Copy your public key**:
   ```bash
   cat ~/.ssh/gcp_freqtrade_key.pub
   ```
9. **Paste the entire public key** into the text field
10. **Click "Save"**

#### Option B: Via SSH (if you have access)

If you can already SSH into the VM:

```bash
# Copy public key to VM
ssh-copy-id -i ~/.ssh/gcp_freqtrade_key.pub USERNAME@VM_IP

# Or manually add to authorized_keys
cat ~/.ssh/gcp_freqtrade_key.pub | ssh USERNAME@VM_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Step 3: Get Private Key Content

**Copy the entire private key** (this is what goes into GitHub Secrets):

```bash
cat ~/.ssh/gcp_freqtrade_key
```

The output should look like:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
NhAAAAAwEAAQAAAYEAv...
...
-----END OPENSSH PRIVATE KEY-----
```

**⚠️ IMPORTANT:** Copy the ENTIRE output including:
- `-----BEGIN OPENSSH PRIVATE KEY-----`
- All the encoded content in the middle
- `-----END OPENSSH PRIVATE KEY-----`

### Step 4: Update GitHub Secret

1. **Go to GitHub**: Repository → Settings → Secrets and variables → Actions
2. **Find** `GCP_SSH_PRIVATE_KEY` secret
3. **Click "Update"**
4. **Paste the entire private key** (from Step 3)
5. **Click "Update secret"**

## Verify Your SSH Key Works

Before updating GitHub secrets, test locally:

```bash
# Test SSH connection with your new key
ssh -i ~/.ssh/gcp_freqtrade_key USERNAME@VM_IP

# If successful, you should see the VM prompt
```

## Troubleshooting

### "Permission denied (publickey)"
- **Cause**: Public key not added to VM, or wrong username
- **Fix**: Verify public key is in VM's `~/.ssh/authorized_keys` file

### "Connection refused" or "Connection timed out"
- **Cause**: VM not accessible, firewall blocking, or wrong IP
- **Fix**: Check VM is running, firewall rules allow SSH (port 22), and IP is correct

### "Host key verification failed"
- **Cause**: VM's host key changed
- **Fix**: Remove old key from `~/.ssh/known_hosts`:
  ```bash
  ssh-keygen -R VM_IP
  ```

### GitHub Actions still failing
- **Check**: Secrets are set at **repository level** (not just environment level)
- **Verify**: Secret value includes entire key (begin/end markers)
- **Test**: Run the workflow again after updating secrets

## Quick Command Reference

```bash
# Generate new key
ssh-keygen -t rsa -b 4096 -C "email@example.com" -f ~/.ssh/gcp_freqtrade_key

# Show public key (to add to VM)
cat ~/.ssh/gcp_freqtrade_key.pub

# Show private key (for GitHub secret)
cat ~/.ssh/gcp_freqtrade_key

# Test SSH connection
ssh -i ~/.ssh/gcp_freqtrade_key USERNAME@VM_IP

# Check if key has correct permissions
ls -la ~/.ssh/gcp_freqtrade_key
# Should show: -rw------- (600)
```

## Security Best Practices

1. **Never commit** private keys to git
2. **Use a passphrase** for extra security
3. **Rotate keys** periodically (every 6-12 months)
4. **Use different keys** for different servers/environments
5. **Restrict key access** on the VM (use `authorized_keys` with specific commands if possible)

