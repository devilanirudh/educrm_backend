# Railway Deployment Guide

This guide will help you deploy the E-School Backend to Railway.

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app))
2. Git repository with your backend code
3. Railway CLI (optional but recommended)

## Deployment Steps

### 1. Connect Your Repository

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Select the `backend` directory as the source

### 2. Configure Environment Variables

In your Railway project dashboard, add these environment variables:

```env
# Required
PORT=8000
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key-change-this

# Database (Railway will provide PostgreSQL)
DATABASE_URL=postgresql://username:password@host:port/database

# CORS (add your frontend URL)
BACKEND_CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000

# Optional - Email Configuration
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
EMAILS_FROM_EMAIL=noreply@yourschool.com

# Optional - Redis (if using Railway Redis)
REDIS_URL=redis://username:password@host:port

# Optional - Payment Gateway
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key

# Optional - SMS (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-phone
```

### 3. Deploy

1. Railway will automatically detect the Dockerfile and build your application
2. The deployment will start automatically
3. Monitor the build logs for any issues

### 4. Verify Deployment

1. Check the deployment logs in Railway dashboard
2. Visit your application URL (provided by Railway)
3. Test the health endpoint: `https://your-app.railway.app/`
4. Check API docs: `https://your-app.railway.app/docs`

## Troubleshooting

### Common Issues

1. **Build Failures**: Check the build logs for missing dependencies
2. **Database Connection**: Ensure DATABASE_URL is correctly set
3. **Port Issues**: Railway sets PORT automatically, don't override it
4. **CORS Errors**: Update BACKEND_CORS_ORIGINS with your frontend URL

### Logs

- View logs in Railway dashboard under "Deployments"
- Use Railway CLI: `railway logs`

### Database Migration

The application will automatically create tables on first run. For production:

1. Consider using Railway's PostgreSQL service
2. Update DATABASE_URL to use PostgreSQL instead of DuckDB
3. Run migrations manually if needed

## Custom Domains

1. Go to your Railway project settings
2. Add a custom domain
3. Update your DNS records
4. Update CORS settings with the new domain

## Monitoring

- Railway provides basic monitoring
- Check the "Metrics" tab for performance data
- Set up alerts for downtime

## Security Notes

- Change the default SECRET_KEY
- Use strong passwords for all services
- Enable HTTPS (Railway provides this automatically)
- Regularly update dependencies

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
