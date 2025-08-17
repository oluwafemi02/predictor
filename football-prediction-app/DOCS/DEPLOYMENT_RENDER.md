# Deployment Guide - Render

This guide covers deploying the Football Prediction App to Render.

## Prerequisites

- GitHub repository with your code
- Render account (free tier works)
- PostgreSQL database (Render provides this)
- Redis instance (Render provides this)
- API keys for SportMonks and RapidAPI (if using odds)

## Overview

We'll deploy:
1. PostgreSQL database
2. Redis instance
3. Backend web service
4. Frontend static site
5. Background worker (optional)

## Step 1: Database Setup

1. **Create PostgreSQL Database**
   - Go to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Choose a name (e.g., `football-predictions-db`)
   - Select region closest to you
   - Choose plan (free tier available)
   - Click "Create Database"

2. **Note the connection string**
   - Copy the "External Database URL"
   - This will be your `DATABASE_URL`

## Step 2: Redis Setup

1. **Create Redis Instance**
   - Click "New +" → "Redis"
   - Choose a name (e.g., `football-predictions-redis`)
   - Select same region as database
   - Choose plan (free tier available)
   - Click "Create Redis"

2. **Note the connection string**
   - Copy the "Redis URL"
   - This will be your `REDIS_URL`

## Step 3: Backend Deployment

1. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     ```
     Name: football-predictions-backend
     Region: Same as database
     Branch: main (or your default)
     Root Directory: ./backend
     Environment: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: gunicorn wsgi:app
     ```

2. **Add Environment Variables**
   Go to "Environment" tab and add:
   ```
   DATABASE_URL=<your-postgres-url>
   REDIS_URL=<your-redis-url>
   SPORTMONKS_API_KEY=<your-api-key>
   RAPIDAPI_KEY=<your-api-key>
   SECRET_KEY=<generate-a-secret-key>
   TOKEN_ENCRYPTION_PASSWORD=<generate-a-password>
   TOKEN_ENCRYPTION_SALT=<generate-a-salt>
   FLASK_ENV=production
   PYTHONUNBUFFERED=1
   CORS_ORIGINS=https://your-frontend.onrender.com,https://*.onrender.com
   ```

3. **Configure Health Check**
   - Path: `/healthz`
   - Timeout: 300 seconds (for startup)

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build and deployment

## Step 4: Frontend Deployment

1. **Create Static Site**
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Configure:
     ```
     Name: football-predictions-frontend
     Branch: main
     Root Directory: ./frontend
     Build Command: npm install && npm run build
     Publish Directory: ./dist
     ```

2. **Add Environment Variables**
   ```
   VITE_API_BASE_URL=https://your-backend.onrender.com
   ```

3. **Add Redirects**
   Create `frontend/public/_redirects`:
   ```
   /* /index.html 200
   ```

4. **Deploy**
   - Click "Create Static Site"
   - Wait for build and deployment

## Step 5: Background Worker (Optional)

For Celery workers:

1. **Create Background Worker**
   - Click "New +" → "Background Worker"
   - Connect repository
   - Configure:
     ```
     Name: football-predictions-worker
     Root Directory: ./backend
     Environment: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: celery -A celery_app worker --loglevel=info
     ```

2. **Add same environment variables as backend**

## Configuration Files

### Backend render.yaml
```yaml
services:
  - type: web
    name: football-predictions-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn wsgi:app
    healthCheckPath: /healthz
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: football-predictions-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: football-predictions-redis
          type: redis
          property: connectionString
```

### Frontend Build Settings
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Auto-Deploy: Yes (on push to main)

## Environment Variables Reference

### Required for Production
```bash
# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# API Keys
SPORTMONKS_API_KEY=your_key
RAPIDAPI_KEY=your_key  # If using odds

# Security
SECRET_KEY=generate_random_string
TOKEN_ENCRYPTION_PASSWORD=generate_random_string
TOKEN_ENCRYPTION_SALT=generate_random_string

# Flask
FLASK_ENV=production
PYTHONUNBUFFERED=1

# CORS
CORS_ORIGINS=https://your-frontend.onrender.com
```

### Optional
```bash
# Scheduler
ENABLE_SCHEDULER=true

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO
```

## Post-Deployment Steps

1. **Run Database Migrations**
   - Go to backend service
   - Click "Shell" tab
   - Run:
     ```bash
     flask db upgrade
     ```

2. **Verify Health**
   - Visit: `https://your-backend.onrender.com/healthz`
   - Should return: `{"status": "ok"}`

3. **Check Version**
   - Visit: `https://your-backend.onrender.com/api/version`
   - Verify features are enabled

4. **Test CORS**
   - Open frontend
   - Check browser console for CORS errors
   - Adjust CORS_ORIGINS if needed

## Monitoring

1. **Logs**
   - Each service has a "Logs" tab
   - Check for startup errors
   - Monitor for runtime issues

2. **Metrics**
   - Render provides basic metrics
   - Monitor memory and CPU usage
   - Set up alerts for downtime

3. **Health Checks**
   - `/healthz` - Simple health check
   - `/api/health` - Detailed health status

## Troubleshooting

### Build Failures
- Check Python version matches requirements
- Verify all dependencies in requirements.txt
- Check for binary dependencies

### Startup Failures
- Check environment variables
- Verify database connection
- Check logs for ImportError

### CORS Issues
- Verify CORS_ORIGINS includes frontend URL
- Check for trailing slashes
- Use wildcard for development: `https://*.onrender.com`

### Database Issues
- Verify DATABASE_URL format
- Check connection limits
- Run migrations: `flask db upgrade`

### Performance Issues
- Enable caching with Redis
- Add database indexes
- Upgrade to paid tier for more resources

## Scaling

### Horizontal Scaling
- Increase instance count in service settings
- Use Redis for session storage
- Ensure stateless application

### Vertical Scaling
- Upgrade to higher tier
- More RAM for ML models
- More CPU for predictions

### Caching Strategy
- Use Redis aggressively
- Cache predictions for 30 minutes
- Cache team/player data for 24 hours

## Security Checklist

- [ ] Strong SECRET_KEY
- [ ] HTTPS enforced
- [ ] Environment variables not in code
- [ ] Database backups enabled
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] API keys rotated regularly

## Cost Optimization

1. **Free Tier Limits**
   - 750 hours/month
   - Sleep after 15 min inactivity
   - Limited CPU/RAM

2. **Optimization Tips**
   - Use caching extensively
   - Optimize database queries
   - Compress static assets
   - Use CDN for frontend

3. **When to Upgrade**
   - Consistent traffic
   - Need background jobs
   - Require more reliability

## Maintenance

1. **Regular Updates**
   - Update dependencies monthly
   - Monitor for security patches
   - Test before deploying

2. **Database Maintenance**
   - Regular backups
   - Monitor growth
   - Optimize queries

3. **Monitoring**
   - Set up uptime monitoring
   - Configure alerts
   - Track performance metrics

## Support

For Render-specific issues:
- Check Render status page
- Review Render documentation
- Contact Render support

For application issues:
- Check application logs
- Review error messages
- Test locally first