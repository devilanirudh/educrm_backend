#!/bin/bash

# Railway Environment Variables Setup Script
# Run this script to set up the required environment variables on Railway

echo "🚀 Setting up Railway Environment Variables for E-School Backend"
echo "================================================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed. Please install it first:"
    echo "   npm install -g @railway/cli"
    echo "   Then run: railway login"
    exit 1
fi

echo "✅ Railway CLI found"

# Set environment variables
echo "📝 Setting environment variables..."

# Required variables
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set SECRET_KEY="your-production-secret-key-change-this-$(date +%s)"

# CORS configuration for Vercel frontend
railway variables set BACKEND_CORS_ORIGINS="https://educrm-frontend.vercel.app,https://educrm-frontend-git-main.vercel.app,https://*.vercel.app,http://localhost:3000"

# Trusted hosts
railway variables set ALLOWED_HOSTS="localhost,127.0.0.1,educrmbackend-production.up.railway.app,educrm-frontend.vercel.app,*.vercel.app"

echo "✅ Environment variables set successfully!"

echo ""
echo "🔧 Next steps:"
echo "1. Deploy your application: railway up"
echo "2. Check the deployment logs: railway logs"
echo "3. Test the API: https://educrmbackend-production.up.railway.app/"
echo "4. Test CORS with your frontend: https://educrm-frontend.vercel.app"
echo ""
echo "📚 For more information, see: RAILWAY_DEPLOYMENT.md"
