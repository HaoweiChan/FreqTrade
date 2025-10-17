# FreqUI Troubleshooting Guide

## Issue Summary

After implementing nginx authentication and bot connection fixes, the production site (http://104.199.142.182:8080/) continues to show the default nginx welcome page despite 4 successful deployments.

## Fixes Implemented ✅

### 1. Bot Connection URLs
- **File**: `ui/init-bots.js`
- **Changes**: Updated bot URLs from direct port access (`:8081-8085`) to nginx reverse proxy paths (`:8080/api/ichiv1/`, etc.) with trailing slashes
- **Commit**: `59d9147`

### 2. Nginx Configuration
- **File**: `ui/nginx/nginx.conf`
- **Changes**:
  - Added HTTP Basic Authentication (`auth_basic`, `.htpasswd`)
  - Added explicit HTTP method support (GET, POST, PUT, DELETE, PATCH, OPTIONS)
  - Added WebSocket support
  - Added Authorization header forwarding
  - Added DNS resolver for dynamic upstream resolution
  - Added `daemon off` directive
- **Commits**: `59d9147`, `74d433a`

### 3. Dockerfile Paths
- **File**: `ui/Dockerfile`
- **Changes**:
  - Fixed file paths from `/etc/nginx/html/` to `/usr/share/nginx/html/`
  - Added `.htpasswd` generation
- **Commits**: `59d9147`, `9c4a13f`

### 4. CI/CD Pipeline
- **File**: `.github/workflows/ci-cd.yml`
- **Changes**:
  - Updated UI test to handle authentication (check for 401 without credentials, 200 with credentials)
  - Updated integration test to handle authentication
- **Commits**: `213a2d1`, `aeb210d`

### 5. Deployment Process
- **File**: `scripts/deploy.sh`
- **Changes**: Removed Step 3 that rebuilt UI locally, now only uses pulled images
- **Commit**: `bcd785e`

### 6. Docker Compose
- **File**: `docker-compose.yml`
- **Changes**: Commented out `build` section for frequi service to force registry image usage
- **Commit**: `3e8bc67`

## Current Status ❌

**Problem**: Production site still shows "Welcome to nginx!" default page

**Evidence**:
- All CI/CD tests pass ✅
- Images build successfully ✅
- Deployments complete successfully ✅
- Containers start successfully ✅
- But website shows default nginx page ❌

## Suspected Root Cause

The base Docker image `FROM freqtradeorg/frequi:latest` may:
1. Not contain the actual FreqUI application
2. Have incorrect directory structure
3. Have an entrypoint that overrides our configuration
4. Be serving from unexpected location

## Diagnostic Steps

### Test Base Image
```bash
# On production server
docker pull freqtradeorg/frequi:latest
docker run -d -p 9999:80 --name test-freq freqtradeorg/frequi:latest
sleep 5
curl http://localhost:9999
docker logs test-freq
docker stop test-freq && docker rm test-freq
```

If this shows the default nginx page, the base image itself is the problem.

### Run Diagnostic Script
```bash
cd /home/*/freqtrade
./scripts/diagnose-ui.sh
```

This will check:
- Container status
- Nginx logs
- Configuration files
- HTML file locations
- Actual image being used

### Manual Container Inspection
```bash
# Check what's actually running
docker exec freqtrade-ui ls -la /usr/share/nginx/html/
docker exec freqtrade-ui cat /etc/nginx/nginx.conf
docker exec freqtrade-ui cat /usr/share/nginx/html/index.html | head -20
docker logs freqtrade-ui
```

## Potential Solutions

### Option 1: Build FreqUI from Scratch
Instead of using `freqtradeorg/frequi:latest`, clone and build FreqUI:

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
RUN apk add --no-cache git
RUN git clone https://github.com/freqtrade/frequi.git .
RUN npm install
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
RUN apk add --no-cache apache2-utils && \
    htpasswd -bc /etc/nginx/.htpasswd "admin" "admin123" && \
    apk del apache2-utils
```

### Option 2: Use Official FreqUI Build Process
Check FreqUI documentation: https://github.com/freqtrade/frequi

### Option 3: Different Base Image
Try nginx official image and manually add FreqUI files.

## Files Modified

All changes committed to main branch:
- `ui/init-bots.js`
- `ui/Dockerfile`
- `ui/nginx/nginx.conf`
- `.github/workflows/ci-cd.yml`
- `scripts/deploy.sh`
- `docker-compose.yml`

## Testing Checklist

- [x] Local docker build works
- [x] CI/CD tests pass
- [x] Authentication works locally
- [x] Images pushed to registry
- [x] Deployment completes successfully
- [x] Containers start on production
- [ ] Website shows FreqUI (FAILING)
- [ ] Nginx authentication prompts (UNTESTED - blocked by above)
- [ ] Bots show as online (UNTESTED - blocked by above)

## Next Steps

1. **Immediate**: Run diagnostic script on production server
2. **Short-term**: Test base image to confirm if it's the issue
3. **Long-term**: Consider building FreqUI from source instead of using pre-built image

## Contact

Created: 2025-10-17
Last Updated: 2025-10-17
Status: INVESTIGATING BASE IMAGE ISSUE

