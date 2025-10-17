# GitHub Actions Secrets - How They Work

## 🔐 How GitHub Actions Loads Secrets

GitHub Actions secrets are **encrypted environment variables** that are securely injected into your workflow runs.

## 📋 Secret Loading Process

### 1. **Secret Storage**
- Secrets are stored **encrypted** in GitHub's secure database
- Only visible to repository administrators and the workflow runtime
- **Never logged** in console output or workflow logs

### 2. **Runtime Injection**
When a workflow runs, GitHub Actions:
1. **Decrypts** the secrets for that specific run
2. **Injects them as environment variables** into the runner's environment
3. **Makes them available** via `secrets` context in workflow YAML

### 3. **Access in Workflows**
```yaml
# Access via secrets context
${{ secrets.SECRET_NAME }}

# Example in our workflow:
credentials_json: ${{ secrets.GCP_SA_KEY }}
username: ${{ github.actor }}
password: ${{ secrets.GITHUB_TOKEN }}
```

## 🛡️ Security Features

### **Automatic Masking**
- Secrets are **automatically masked** in logs
- If accidentally printed, they show as `***`
- Example: `password: ***`

### **Scope Limitations**
- Secrets are **only available** to the specific workflow run
- **Not accessible** to other repositories or users
- **Not inherited** by forked repositories (unless explicitly allowed)

### **Fork Protection**
By default, secrets are **not passed** to workflows triggered from forks for security reasons.

## 🔧 Using Secrets in Our Pipeline

### **Current Secret Usage:**
```yaml
# GCP Authentication
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}

# SSH Access
echo "${{ secrets.GCP_SSH_PRIVATE_KEY }}" > /tmp/gcp_key

# Trading Bot Config
- FREQTRADE__EXCHANGE__KEY=${{ secrets.BINANCE_KEY }}
- FREQTRADE__TELEGRAM__TOKEN=${{ secrets.TELEGRAM_TOKEN }}
```

### **Secret Categories in Our Pipeline:**

1. **GCP Authentication**
   - `GCP_SA_KEY` - Service account JSON
   - `GCP_PROJECT_ID` - Project identifier

2. **GCP VM Access**
   - `GCP_VM_IP` - VM external IP
   - `GCP_VM_USER` - SSH username
   - `GCP_SSH_PRIVATE_KEY` - SSH private key

3. **Trading Bot Configuration**
   - `BINANCE_KEY` & `BINANCE_SECRET`
   - `TELEGRAM_TOKEN` & `TELEGRAM_CHAT_ID`
   - `FT_UI_USERNAME` & `FT_UI_PASSWORD`

## 🚨 Important Security Notes

### **Never Log Secrets**
```yaml
# ❌ DANGEROUS - Don't do this!
- name: Debug
  run: echo "API Key: ${{ secrets.BINANCE_KEY }}"

# ✅ SAFE - Use for non-sensitive info only
- name: Debug
  run: echo "Project ID: ${{ secrets.GCP_PROJECT_ID }}"
```

### **Secret Rotation**
- Regularly rotate secrets (especially API keys)
- Update GitHub secrets when rotating
- Use different secrets for different environments

### **Access Control**
- **Repository Settings** → **Secrets and variables** → **Actions**
- Only repository admins can view/manage secrets
- Consider using **environments** for production secrets

## 🔍 Debugging Secret Issues

### **Check if Secret Exists**
```yaml
- name: Verify secrets
  run: |
    if [ -z "${{ secrets.GCP_SA_KEY }}" ]; then
      echo "❌ GCP_SA_KEY secret not found"
      exit 1
    fi
    echo "✅ All required secrets are available"
```

### **Conditional Job Execution**
```yaml
deploy-to-gcp:
  if: secrets.GCP_SA_KEY != ''
  # Only runs if secret exists
```

## 📚 Best Practices

1. **Use Descriptive Names**: `BINANCE_API_KEY` instead of `KEY_1`
2. **Group Related Secrets**: Use consistent prefixes (`GCP_`, `BINANCE_`)
3. **Document Required Secrets**: Keep `docs/gcp-secrets-setup.md` updated
4. **Regular Rotation**: Set calendar reminders to rotate secrets
5. **Environment Separation**: Use different secrets for dev/staging/prod

## 🎯 Summary

GitHub Actions secrets provide a **secure, encrypted way** to store sensitive configuration that your workflows need. They are:

- ✅ **Encrypted at rest** in GitHub's database
- ✅ **Automatically injected** into workflow environment
- ✅ **Masked in logs** for security
- ✅ **Scoped to repository** and workflow runs only
- ✅ **Essential for production deployments**

The secrets are **automatically loaded** by GitHub Actions runtime and made available through the `secrets` context in your workflow YAML files.
