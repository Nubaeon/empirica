#!/bin/bash
# Secure startup script for Empirica multi-AI system

set -e

EMPIRICA_ROOT="/home/yogapad/empirical-ai/empirica"
cd "$EMPIRICA_ROOT"

echo "🚀 Starting Empirica Secure Multi-AI System..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install: sudo apt install docker.io"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Install: sudo apt install docker-compose"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env and add your API keys:"
    echo "   nano .env"
    exit 1
fi

echo "✅ Prerequisites met"
echo ""

# Create workspace if needed
echo "📁 Creating workspace directory..."
mkdir -p workspace
echo "✅ Workspace ready"
echo ""

# Pull/build images
echo "🐳 Pulling Docker images..."
docker-compose pull || true
echo "✅ Images ready"
echo ""

# Start services
echo "🏃 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check health
echo ""
echo "🔍 Checking service health..."

if docker ps | grep -q "empirica-api-gateway"; then
    echo "✅ API Gateway: running"
else
    echo "❌ API Gateway: failed"
    docker-compose logs empirica-api
    exit 1
fi

if docker ps | grep -q "empirica-sentinel"; then
    echo "✅ Sentinel: running"
else
    echo "⚠️  Sentinel: not running (optional)"
fi

if docker ps | grep -q "vibe-worker"; then
    echo "✅ Vibe: running"
else
    echo "⚠️  Vibe: not running (optional)"
fi

if docker ps | grep -q "rovodev-worker"; then
    echo "✅ Rovodev: running"
else
    echo "⚠️  Rovodev: not running (optional)"
fi

echo ""
echo "✅ Empirica Secure Multi-AI System is running!"
echo ""
echo "📊 Useful commands:"
echo "   docker-compose ps              # Check status"
echo "   docker-compose logs -f         # View all logs"
echo "   docker-compose logs -f sentinel  # View Sentinel alerts"
echo "   docker-compose stop            # Stop all services"
echo "   docker-compose down            # Stop and remove containers"
echo ""
echo "🔐 Security monitoring:"
echo "   curl http://localhost:8000/sentinel/status"
echo "   docker-compose logs sentinel | grep -E 'ALERT|BLOCK'"
echo ""
echo "📖 Full documentation: DOCKER_SECURITY_SETUP.md"
