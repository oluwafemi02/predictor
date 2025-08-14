# SportMonks Integration Deployment Guide for Render

This guide will walk you through deploying the SportMonks integration to Render.

## Prerequisites

1. A Render account (https://render.com)
2. Your SportMonks API token ready
3. Access to your GitHub repository

## Step 1: Connect Your GitHub Repository

1. Log in to your Render dashboard
2. Click "New +" and select "Blueprint"
3. Connect your GitHub account if not already connected
4. Select your repository: `oluwafemi02/predictor`
5. Select the branch: `cursor/research-sportmonks-api-for-web-app-eb28`
6. Name your blueprint: "Football Prediction with SportMonks"
7. Click "Apply"

## Step 2: Configure Environment Variables

After the blueprint is created, you'll need to set the following environment variables:

### For the Backend Service (football-prediction-backend):

1. Go to the backend service in your Render dashboard
2. Navigate to "Environment" tab
3. Add these environment variables:

```
SPORTMONKS_API_KEY=cCo0Sn0Fj6BnSmdigHu0oveKznsuZMZzXYe0jIaDDmo8ZymwBP7XjFZCYJPh
SPORTMONKS_FALLBACK_TOKENS=token1,token2,token3  # Add any backup tokens here
RAPIDAPI_KEY=your_rapidapi_key_here  # If you have one
FOOTBALL_API_KEY=your_football_api_key_here  # If you have one
```

### For the Scheduler Service (football-prediction-scheduler):

The scheduler will automatically inherit the SportMonks tokens from the backend service.

## Step 3: Initialize the Database

1. Once the services are deployed, go to your backend service
2. Click on "Shell" tab
3. Run the following commands:

```bash
# Create SportMonks tables
python migrations/add_sportmonks_tables.py create

# Initialize some data (optional)
python -c "from app import create_app; from sportmonks_scheduler import sportmonks_scheduler; app = create_app(); sportmonks_scheduler.init_app(app); sportmonks_scheduler.run_initial_updates()"
```

## Step 4: Verify Services

### Check Backend API:
- Visit: `https://football-prediction-backend.onrender.com/api/sportmonks/health`
- You should see a JSON response with API health status

### Check Frontend:
- Visit: `https://football-prediction-frontend.onrender.com/sportmonks`
- You should see the SportMonks dashboard with tabs for Live Scores, Predictions, and Value Bets

### Check Redis:
- In Render dashboard, check the Redis service logs
- Should show successful connections from backend

### Check Scheduler:
- In Render dashboard, check the scheduler worker logs
- Should show "SportMonks scheduler started" and initial update messages

## Step 5: Monitor and Troubleshoot

### Common Issues and Solutions:

1. **"No predictions available"**
   - Check if SportMonks API key is correctly set
   - Verify scheduler is running and updating data
   - Check backend logs for API errors

2. **Redis connection errors**
   - Ensure Redis service is running
   - Check REDIS_URL is correctly set in environment variables

3. **CORS errors**
   - Update CORS_ORIGINS in backend environment to include your frontend URL
   - Current setting: `https://football-prediction-frontend.onrender.com,https://football-prediction-frontend-zx5z.onrender.com`

4. **Database errors**
   - Ensure PostgreSQL database is running
   - Run migration script if tables are missing

## Step 6: Production Optimizations

Once everything is working, consider these optimizations:

1. **Upgrade Services**:
   - Upgrade database from free to Starter ($7/month) for better performance
   - Upgrade Redis from free to Starter ($10/month) for more memory
   - Upgrade web services for more resources

2. **Configure Alerts**:
   - Set up health check alerts in Render
   - Configure failure notifications

3. **Security**:
   - Rotate API tokens periodically
   - Set strong TOKEN_ENCRYPTION_PASSWORD
   - Review and update INTERNAL_API_KEYS

## API Endpoints

Your SportMonks integration provides these endpoints:

- `GET /api/sportmonks/health` - API health check
- `GET /api/sportmonks/fixtures/live` - Live match scores
- `GET /api/sportmonks/fixtures/upcoming` - Upcoming fixtures with predictions
- `GET /api/sportmonks/predictions/{fixture_id}` - Detailed predictions
- `GET /api/sportmonks/value-bets` - Value betting opportunities
- `GET /api/sportmonks/standings/{league_id}` - League standings
- `GET /api/sportmonks/teams/{team_id}` - Team details
- `GET /api/sportmonks/leagues` - Available leagues

## Monitoring

- **Backend Logs**: Check for API requests and errors
- **Scheduler Logs**: Monitor data synchronization
- **Redis Monitor**: Track cache hit rates
- **Database Queries**: Monitor slow queries

## Support

If you encounter issues:
1. Check service logs in Render dashboard
2. Verify environment variables are set correctly
3. Ensure all services are running (Backend, Frontend, Scheduler, Redis, Database)
4. Check SportMonks API status at https://docs.sportmonks.com/football/

## Next Steps

1. Customize the prediction thresholds in the frontend
2. Add more leagues to the scheduler (currently tracking major European leagues)
3. Implement email alerts for high-value bets
4. Add user authentication for personalized features
5. Set up analytics to track prediction accuracy

Congratulations! Your SportMonks integration is now deployed on Render.