#!/bin/bash

echo "=== FreqUI Diagnostic Script ==="
echo ""

echo "1. Checking container status:"
docker ps | grep freqtrade

echo ""
echo "2. Checking freqtrade-ui logs (last 50 lines):"
docker logs --tail 50 freqtrade-ui

echo ""
echo "3. Checking nginx configuration in container:"
docker exec freqtrade-ui cat /etc/nginx/nginx.conf | head -30

echo ""
echo "4. Checking HTML files location:"
docker exec freqtrade-ui ls -la /usr/share/nginx/html/ | head -20

echo ""
echo "5. Checking alternate HTML location:"
docker exec freqtrade-ui ls -la /etc/nginx/html/ 2>&1 | head -20

echo ""
echo "6. Checking what image is actually running:"
docker inspect freqtrade-ui | grep -A 5 "Image"

echo ""
echo "7. Testing HTTP response from inside container:"
docker exec freqtrade-ui curl -I http://localhost 2>&1

echo ""
echo "=== End Diagnostic ==="

