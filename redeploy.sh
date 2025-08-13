#!/bin/bash

# Redeploy Backend Script
# This script helps redeploy the backend with the latest changes

echo "🚀 Redeploying E-School Backend with Latest Changes"
echo "=================================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed. Please install it first:"
    echo "   npm install -g @railway/cli"
    echo "   Then run: railway login"
    exit 1
fi

echo "✅ Railway CLI found"

# Check if we're in the backend directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Please run this script from the backend directory"
    exit 1
fi

echo "📝 Setting environment variables for production..."

# Set production environment variables
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set BACKEND_CORS_ORIGINS="https://educrm-frontend.vercel.app,https://educrm-frontend-git-main.vercel.app,https://*.vercel.app,http://localhost:3000"
railway variables set ALLOWED_HOSTS="localhost,127.0.0.1,educrmbackend-production.up.railway.app,educrm-frontend.vercel.app,*.vercel.app"

echo "✅ Environment variables set"

echo "🔨 Building and deploying..."

# Deploy to Railway
railway up

echo "✅ Deployment completed!"

echo ""
echo "🔧 Testing the deployment..."
echo "1. Health check: https://educrmbackend-production.up.railway.app/"
echo "2. API docs: https://educrmbackend-production.up.railway.app/docs"
echo "3. Classes endpoint: https://educrmbackend-production.up.railway.app/api/v1/classes"
echo ""

echo "📊 Check deployment logs:"
echo "   railway logs"
echo ""
echo "🌐 Your frontend should now be able to connect to the backend!"
