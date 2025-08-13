# Football Prediction Backend - Render Deployment Guide

This guide explains how to deploy the Football Prediction Backend to Render.com.

## Prerequisites

1. A GitHub account with this repository
2. A Render.com account (free tier is sufficient)
3. Your repository connected to Render.com

## Deployment Steps

### 1. Push to GitHub

First, ensure all your changes are committed and pushed to GitHub:

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Create New Web Service on Render

1. Go to your [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Select the repository containing this backend code

### 3. Configure the Service

Render should automatically detect the `render.yaml` file. If not, use these settings:

- **Name**: `football-prediction-backend` (or your preferred name)
- **Environment**: `Python`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: Free

### 4. Environment Variables

The following environment variables will be set automatically:
- `DATABASE_URL` (from the PostgreSQL database)
- `SECRET_KEY` (auto-generated)
- `PYTHON_VERSION` (3.11.0)
- `FLASK_ENV` (production)

You need to manually add:
- `RAPIDAPI_KEY`: Your RapidAPI key for football data
- `CORS_ORIGINS`: Comma-separated list of allowed frontend URLs (e.g., `https://your-frontend.onrender.com`)

To add environment variables:
1. Go to your service's Settings tab
2. Click "Environment" 
3. Add the required variables

### 5. Database Setup

The `render.yaml` file includes a PostgreSQL database that will be created automatically. The database connection will be handled through the `DATABASE_URL` environment variable.

### 6. Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Create a PostgreSQL database
   - Install Python dependencies
   - Run the build script (database initialization)
   - Start the Gunicorn server

### 7. Access Your API

Once deployed, your API will be available at:
- `https://your-service-name.onrender.com`

Test it by visiting:
- `https://your-service-name.onrender.com/` - API info
- `https://your-service-name.onrender.com/api/v1/odds/leagues` - List leagues

## Important Notes

### Free Tier Limitations

- The free tier spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- Limited to 750 hours/month
- PostgreSQL database limited to 90 days of data retention

### Production Considerations

For production use, consider:
1. Upgrading to a paid plan for always-on service
2. Setting up proper logging and monitoring
3. Implementing rate limiting
4. Adding authentication for sensitive endpoints
5. Setting up a CDN for static assets

### Troubleshooting

1. **Database Connection Issues**: 
   - Check that `DATABASE_URL` is properly set
   - Ensure the database is created and running

2. **Import Errors**:
   - Check `requirements.txt` for all dependencies
   - Ensure Python version matches (3.11.0)

3. **CORS Issues**:
   - Add your frontend URL to `CORS_ORIGINS` environment variable

4. **Build Failures**:
   - Check the build logs in Render dashboard
   - Ensure `build.sh` is executable (`chmod +x build.sh`)

## Updating the Deployment

To update your deployed service:
1. Push changes to GitHub
2. Render will automatically detect and redeploy

Or manually trigger a deploy from the Render dashboard.

## Monitoring

- View logs in the Render dashboard
- Set up alerts for downtime
- Monitor database usage to stay within free tier limits

## Support

For Render-specific issues: https://render.com/docs
For application issues: Check the repository issues page