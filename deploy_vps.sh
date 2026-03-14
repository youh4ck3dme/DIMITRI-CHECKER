#!/bin/bash

# V4-FINSTAT PROJEKT - Automated VPS Deployment Script
# IP: 194.182.87.6

echo "🚀 Starting deployment of V4-FINSTAT PROJEKT v5.0..."

# 1. Update repository
echo "📥 Pulling latest changes from git..."
git pull origin main

# 2. Stop and remove old containers
echo "🛑 Stopping current services..."
docker-compose down --remove-orphans

# 3. Build and Start Services
echo "🏗️ Building and starting containers (Production Mode)..."
# We use --build to ensure all changes in Dockerfiles and code are captured
docker-compose up -d --build

# 4. Success Check
echo "🔍 Checking container status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "✅ Deployment completed successfully!"
echo "🌐 API is running on port 8000"
echo "🌐 Web Interface is running on port 80"
echo "📊 Monitoring logs: docker-compose logs -f"

# 5. Cleanup
echo "🧹 Cleaning up dangling images..."
docker image prune -f
