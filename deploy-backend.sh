#!/bin/bash

echo "=========================================="
echo "  🚀 Deploying Backend to Fly.io"
echo "=========================================="
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed!"
    echo "Install it with: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io!"
    echo "Run: flyctl auth login"
    exit 1
fi

echo "✅ Flyctl is installed and you're logged in"
echo ""

# Check if app exists
if ! flyctl status -a martins-system-backend &> /dev/null; then
    echo "📦 App doesn't exist. Creating..."
    echo ""
    echo "⚠️  You'll need to create the app first:"
    echo "   1. Run: flyctl launch --no-deploy"
    echo "   2. Choose app name: martins-system-backend"
    echo "   3. Choose region: jnb (Johannesburg)"
    echo "   4. Then run this script again"
    exit 1
fi

echo "✅ App exists: martins-system-backend"
echo ""

# Check for volume
echo "📊 Checking for data volume..."
if ! flyctl volumes list -a martins-system-backend | grep -q "ecowas_data"; then
    echo "⚠️  No data volume found!"
    echo ""
    read -p "Create 1GB volume for database? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating volume..."
        flyctl volumes create ecowas_data --region jnb --size 1 -a martins-system-backend
        echo "✅ Volume created!"
    else
        echo "❌ Volume required for deployment. Exiting."
        exit 1
    fi
else
    echo "✅ Data volume exists"
fi

echo ""

# Check for required secrets
echo "🔐 Checking secrets..."
SECRETS=$(flyctl secrets list -a martins-system-backend 2>/dev/null)

if ! echo "$SECRETS" | grep -q "SECRET_KEY"; then
    echo "⚠️  SECRET_KEY not set!"
    echo ""
    read -p "Set SECRET_KEY now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Generate a random secret key
        SECRET_KEY=$(openssl rand -base64 32)
        flyctl secrets set SECRET_KEY="$SECRET_KEY" -a martins-system-backend
        echo "✅ SECRET_KEY set!"
    fi
fi

if ! echo "$SECRETS" | grep -q "JWT_SECRET_KEY"; then
    echo "⚠️  JWT_SECRET_KEY not set!"
    echo ""
    read -p "Set JWT_SECRET_KEY now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Generate a random JWT secret
        JWT_SECRET=$(openssl rand -base64 32)
        flyctl secrets set JWT_SECRET_KEY="$JWT_SECRET" -a martins-system-backend
        echo "✅ JWT_SECRET_KEY set!"
    fi
fi

echo ""
echo "🚀 Deploying backend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Deploy
flyctl deploy -a martins-system-backend

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ Backend Deployed Successfully!"
    echo "=========================================="
    echo ""
    echo "📍 Your backend is live at:"
    echo "   https://martins-system-backend.fly.dev"
    echo ""
    echo "📚 API Documentation:"
    echo "   https://martins-system-backend.fly.dev/docs"
    echo ""
    echo "🔍 Next steps:"
    echo "   - Check status: flyctl status -a martins-system-backend"
    echo "   - View logs: flyctl logs -a martins-system-backend"
    echo "   - Deploy frontend: ./deploy-frontend.sh"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check the logs above for errors."
    exit 1
fi
