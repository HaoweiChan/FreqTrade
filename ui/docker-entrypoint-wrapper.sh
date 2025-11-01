#!/bin/sh
# Wrapper script to ensure DNS is properly configured before starting Nginx

# Check if /etc/resolv.conf exists and has a nameserver
if [ -f /etc/resolv.conf ] && grep -q "nameserver" /etc/resolv.conf; then
    echo "DNS configuration found in /etc/resolv.conf"
    cat /etc/resolv.conf
else
    echo "Warning: No DNS configuration found, adding Docker's embedded DNS"
    echo "nameserver 127.0.0.11" > /etc/resolv.conf
fi

# Execute the original entrypoint
exec /docker-entrypoint.sh "$@"

