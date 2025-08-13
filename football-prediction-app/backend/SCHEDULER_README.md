# Football Prediction App - Automated Scheduler

## Overview

The Football Prediction App now includes an automated scheduler that handles:
- Historical data extraction from past seasons
- Upcoming match data updates
- Match result updates
- Automatic model retraining

## Why Automation Was Missing

The original implementation required manual triggering of data extraction and model training because:

1. **MVP Focus**: The initial version was built as a minimum viable product focusing on core functionality
2. **API Rate Limits**: Manual control helped avoid hitting API rate limits during development
3. **Cost Control**: Automated API calls could increase costs with the football-data.org API
4. **Development Simplicity**: Manual triggers made debugging and testing easier

## Scheduler Implementation

### Features

The scheduler now automates the following tasks:

1. **Historical Data Fetch** (Weekly)
   - Fetches data from the last 3 seasons
   - Runs on startup and then weekly
   - Automatically triggers model training if enough data is collected

2. **Upcoming Matches Fetch** (Twice Daily - 9 AM & 6 PM)
   - Fetches matches for the next 30 days
   - Updates match schedules and team information

3. **Match Results Update** (Hourly)
   - Updates scores for recently finished matches
   - Keeps historical data current

4. **Model Training** (Weekly - Sunday 11 PM)
   - Automatically retrains the model with latest data
   - Ensures predictions use the most recent match results

### Configuration

To enable the scheduler, set the environment variable:
```bash
export ENABLE_SCHEDULER=true
```

### Manual Commands

You can also trigger scheduler tasks manually using the management script:

```bash
# Fetch historical data
python manage.py fetch-historical

# Fetch upcoming matches
python manage.py fetch-upcoming

# Update match results
python manage.py update-results

# Train model
python manage.py train-model

# Run scheduler continuously
python manage.py run-scheduler
```

### API Endpoints

Check scheduler status:
```bash
curl http://localhost:5000/api/v1/scheduler/status
```

## PowerShell Commands for Windows

### Train Model via API

```powershell
# Using PowerShell's Invoke-WebRequest
Invoke-WebRequest -Uri "http://localhost:5000/api/v1/model/train" -Method POST -Headers @{"Content-Type"="application/json"} | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Using curl.exe (if installed)
curl.exe -X POST "http://localhost:5000/api/v1/model/train" -H "Content-Type: application/json"
```

### Check Scheduler Status

```powershell
# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:5000/api/v1/scheduler/status" -Method GET | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Using curl.exe
curl.exe "http://localhost:5000/api/v1/scheduler/status"
```

## Running the Scheduler

### Option 1: Enable in Main App

1. Set environment variable:
   ```bash
   export ENABLE_SCHEDULER=true
   ```

2. Start the Flask app normally:
   ```bash
   python app.py
   ```

### Option 2: Run as Separate Process

Run the scheduler in a separate terminal:
```bash
python manage.py run-scheduler
```

This keeps the scheduler isolated from the main web server.

## Important Notes

1. **API Keys Required**: Ensure `FOOTBALL_API_KEY` is set in your environment
2. **Database**: Scheduler requires database access - ensure PostgreSQL is running
3. **Rate Limits**: The football-data.org API has rate limits. The scheduler is configured to respect these
4. **Costs**: Automated API calls may increase your API usage costs

## Troubleshooting

### Frontend Button Not Working

If the "Train Model" button in the frontend doesn't work:

1. **Check CORS**: Ensure the frontend URL is in the CORS_ORIGINS configuration
2. **Check Backend**: Verify the backend is running on the expected port (5000)
3. **Check Console**: Look for errors in the browser developer console
4. **Use API Directly**: Use the PowerShell commands above as a workaround

### Scheduler Not Running

1. Check if `ENABLE_SCHEDULER=true` is set
2. Check logs for any initialization errors
3. Verify all dependencies are installed: `pip install -r requirements.txt`
4. Use `python manage.py run-scheduler` to see detailed error messages

## Future Improvements

Consider implementing:
- Celery for more robust task queuing
- Redis for caching and task distribution
- More granular scheduling controls
- API webhook support for real-time updates
- Automatic season detection and configuration