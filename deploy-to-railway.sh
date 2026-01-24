#!/bin/bash

# Railway Production Deployment Script
# Run this script to deploy Martin System to Railway

set -e

echo "🚀 Martin System - Railway Production Deployment"
echo "================================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Authenticate (if not already)
echo "🔐 Authenticating with Railway..."
railway login

# Create new project or link existing
echo "📦 Setting up Railway project..."
read -p "Create new project? (y/n): " create_new

if [ "$create_new" = "y" ]; then
    railway init
else
    railway link
fi

# Add Redis database
echo "🗄️  Adding Redis database..."
railway add --database redis

# Add PostgreSQL database (if not exists)
echo "🗄️  Adding PostgreSQL database..."
railway add --database postgresql

# Set environment variables
echo "⚙️  Setting environment variables..."
echo "Please provide the following (press Enter to skip if already set):"

read -p "GITHUB_TOKEN: " github_token
[ ! -z "$github_token" ] && railway variables set GITHUB_TOKEN="$github_token"

read -p "VEXA_API_KEY: " vexa_key
[ ! -z "$vexa_key" ] && railway variables set VEXA_API_KEY="$vexa_key"

read -p "RESEND_API_KEY: " resend_key
[ ! -z "$resend_key" ] && railway variables set RESEND_API_KEY="$resend_key"

read -p "PINECONE_API_KEY: " pinecone_key
[ ! -z "$pinecone_key" ] && railway variables set PINECONE_API_KEY="$pinecone_key"

read -p "GOOGLE_CLIENT_ID: " google_id
[ ! -z "$google_id" ] && railway variables set GOOGLE_CLIENT_ID="$google_id"

read -p "GOOGLE_CLIENT_SECRET: " google_secret
[ ! -z "$google_secret" ] && railway variables set GOOGLE_CLIENT_SECRET="$google_secret"

# Generate secure SECRET_KEY for production
echo "🔑 Generating secure SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)
railway variables set SECRET_KEY="$SECRET_KEY"

# Set other required variables
railway variables set LLM_PROVIDER="github"
railway variables set LLM_MODEL="gpt-4o-mini"
railway variables set FRONTEND_URL="https://your-frontend-url.railway.app"

# Deploy backend (web service)
echo "🚀 Deploying backend service..."
cd backend
railway up

# Create worker service
echo "👷 Creating Celery worker service..."
railway service create worker

# Create beat service
echo "⏰ Creating Celery beat service..."
railway service create beat

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Go to Railway dashboard to configure custom domains"
echo "2. Update FRONTEND_URL environment variable with actual frontend URL"
echo "3. Monitor services at: https://railway.app/dashboard"
echo "4. View logs: railway logs --service backend"
echo ""
echo "🎉 Your production system is live!"
