#!/bin/bash
set -e

echo "🔄 Rebuilding FreqUI container with updated configuration..."
cd "$(dirname "$0")/.."

echo "📦 Building frequi image..."
docker-compose build frequi

echo "🔄 Stopping and removing old frequi container..."
docker-compose stop frequi
docker-compose rm -f frequi

echo "🚀 Starting new frequi container..."
docker-compose up -d frequi

echo "⏳ Waiting for container to be ready (10 seconds)..."
sleep 10

echo "✅ Done! FreqUI has been rebuilt and restarted."
echo "📍 Access your UI at: http://104.199.142.182:8080/"
echo "🔐 You should now see the nginx login prompt"
echo ""
echo "🔍 To check logs, run:"
echo "   docker-compose logs -f frequi"

