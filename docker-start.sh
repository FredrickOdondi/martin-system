#!/bin/bash

echo "=========================================="
echo "  🚀 ECOWAS Summit TWG Support System"
echo "  Starting Docker Environment"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file"
        echo "📝 Please update .env with your configuration before continuing"
        echo ""
        read -p "Press Enter to continue or Ctrl+C to abort..."
    else
        echo "❌ Error: .env.example not found!"
        exit 1
    fi
fi

# Check if frontend/.env exists
if [ ! -f frontend/.env ]; then
    echo "⚠️  frontend/.env not found. Creating from frontend/.env.example..."
    if [ -f frontend/.env.example ]; then
        cp frontend/.env.example frontend/.env
        echo "✅ Created frontend/.env file"
    else
        echo "⚠️  Warning: frontend/.env.example not found, using defaults"
    fi
fi

echo ""
echo "🐳 Starting Docker containers..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Services that will start:"
echo "  - PostgreSQL Database (port 5432)"
echo "  - Redis Cache (port 6379)"
echo "  - Backend API (port 8000)"
echo "  - Frontend UI (port 5173)"
echo "  - Celery Worker (background tasks)"
echo "  - Celery Beat (scheduled tasks)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start all services
docker-compose up --build

# Note: Use Ctrl+C to stop all services
