#!/bin/bash
# Entrypoint script to fix strategies symlink issue
# This ensures /freqtrade/user_data/strategies is a directory, not a symlink

# Don't exit on error - let freqtrade handle its own errors
set +e

# Wait a moment for volumes to be fully mounted
sleep 0.5

# Check if /freqtrade/user_data/strategies exists and is a symlink
if [ -L /freqtrade/user_data/strategies ]; then
    echo "WARNING: /freqtrade/user_data/strategies is a symlink, fixing it..."
    TARGET=$(readlink -f /freqtrade/user_data/strategies 2>/dev/null || echo "")
    rm -f /freqtrade/user_data/strategies
    
    # Create directory
    mkdir -p /freqtrade/user_data/strategies
    
    # If target exists and has content, copy it
    if [ -n "$TARGET" ] && [ -d "$TARGET" ] && [ "$(ls -A "$TARGET" 2>/dev/null)" ]; then
        echo "Copying strategies from $TARGET to /freqtrade/user_data/strategies..."
        cp -r "$TARGET"/* /freqtrade/user_data/strategies/ 2>/dev/null || true
    elif [ -d /freqtrade/strategies ] && [ "$(ls -A /freqtrade/strategies 2>/dev/null)" ]; then
        echo "Copying strategies from /freqtrade/strategies to /freqtrade/user_data/strategies..."
        cp -r /freqtrade/strategies/* /freqtrade/user_data/strategies/ 2>/dev/null || true
    fi
fi

# Ensure directory exists (even if symlink wasn't present)
if [ ! -d /freqtrade/user_data/strategies ]; then
    mkdir -p /freqtrade/user_data/strategies
fi

# Re-enable exit on error for the actual command
set -e

# Execute the original command
exec "$@"
