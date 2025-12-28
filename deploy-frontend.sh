#!/bin/bash

echo "=========================================="
echo "  🎨 Deploying Frontend to Fly.io"
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

# Navigate to frontend directory
cd frontend

# Check if app exists
if ! flyctl status -a martins-system-frontend &> /dev/null; then
    echo "📦 App doesn't exist. Creating..."
    echo ""
    echo "⚠️  You'll need to create the app first:"
    echo "   1. Run: cd frontend && flyctl launch --no-deploy"
    echo "   2. Choose app name: martins-system-frontend"
    echo "   3. Choose region: jnb (Johannesburg)"
    echo "   4. Then run this script again"
    exit 1
fi

echo "✅ App exists: martins-system-frontend"
echo ""

echo "🚀 Deploying frontend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Deploy
flyctl deploy -a martins-system-frontend

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ Frontend Deployed Successfully!"
    echo "=========================================="
    echo ""
    echo "📍 Your frontend is live at:"
    echo "   https://martins-system-frontend.fly.dev"
    echo ""
    echo "🔍 Next steps:"
    echo "   - Open app: flyctl apps open -a martins-system-frontend"
    echo "   - Check status: flyctl status -a martins-system-frontend"
    echo "   - View logs: flyctl logs -a martins-system-frontend"
    echo ""
    echo "🎉 Full stack deployment complete!"
    echo ""
    echo "Your app is running:"
    echo "  - Frontend: https://martins-system-frontend.fly.dev"
    echo "  - Backend: https://martins-system-backend.fly.dev"
    echo "  - API Docs: https://martins-system-backend.fly.dev/docs"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check the logs above for errors."
    exit 1
fi

# Return to root directory
cd ..
