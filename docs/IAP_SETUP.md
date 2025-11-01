# IAP Tunneling Setup for GCP VM Access

## The Problem

When using `gcloud compute ssh --tunnel-through-iap`, you might see:
```
Error while connecting [4033: 'not authorized']
```

This means the service account doesn't have permission to use IAP tunneling.

## Solution: Grant IAP Permissions

### Step 1: Find Your Service Account Email

1. Go to GCP Console → IAM & Admin → Service Accounts
2. Find the service account used for GitHub Actions (the one in `GCP_SA_KEY`)
3. Copy the email (e.g., `freqtrade-deployer@your-project.iam.gserviceaccount.com`)

### Step 2: Grant IAP Permission

Run this command (replace with your service account email and project ID):

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:freqtrade-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iap.tunnelResourceAccessor"
```

Or via GCP Console:
1. Go to **IAM & Admin → IAM**
2. Find your service account
3. Click **Edit** (pencil icon)
4. Click **Add Another Role**
5. Search for: `IAP-secured Tunnel User`
6. Select it and click **Save**

### Step 3: Enable IAP API (if not already enabled)

```bash
gcloud services enable iap.googleapis.com --project=YOUR_PROJECT_ID
```

Or via Console:
1. Go to **APIs & Services → Library**
2. Search for "Identity-Aware Proxy API"
3. Click **Enable**

## Alternative: Use Direct SSH (Fallback)

If IAP setup is complex, the workflow will automatically fall back to direct SSH when IAP fails. However, this requires:
- VM has external IP address
- Firewall rules allow port 22 from GitHub Actions runners

## Verify Setup

Test IAP access:

```bash
gcloud compute ssh YOUR_VM_INSTANCE \
  --zone=YOUR_ZONE \
  --tunnel-through-iap \
  --command="echo 'IAP works!'"
```

If successful, you should see "IAP works!" without any authorization errors.

## Current Workflow Behavior

The workflow now:
1. **First tries IAP tunneling** (more secure)
2. **Falls back to direct SSH** if IAP fails (requires external IP)
3. **Provides helpful error messages** if both fail

This ensures maximum compatibility while preferring the more secure IAP method.

