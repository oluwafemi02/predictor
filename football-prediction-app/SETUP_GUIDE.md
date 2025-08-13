# Football Match Prediction App - Setup & Access Guide

## Overview
This is a comprehensive web application that predicts football match outcomes using machine learning. The app uses ensemble ML models (XGBoost, LightGBM, Random Forest, and Gradient Boosting) to analyze team performance, player statistics, injuries, and historical data.

## Technology Stack
- **Backend**: Flask (Python 3.13) with ML libraries
- **Frontend**: React with TypeScript and Material-UI
- **ML Models**: XGBoost, LightGBM, scikit-learn
- **Database**: SQLite (development) / PostgreSQL (production)

## Python Version Compatibility
The application has been configured to work with Python 3.13. While earlier versions (3.8-3.11) may also work, we've created a compatible requirements file that ensures all ML dependencies work properly with Python 3.13.

## Current Status
✅ Backend server is running on http://localhost:5000
✅ Frontend server is running on http://localhost:3000
✅ All ML dependencies are installed and compatible
✅ API is accessible and responding

## Step-by-Step Access Instructions

### 1. Access the Web Application

Open your web browser and navigate to:
```
http://localhost:3000
```

This will load the React frontend application.

### 2. Available Features

The application provides the following features:

- **Dashboard**: View upcoming predictions and recent results
- **Predictions**: Browse all match predictions with filtering options
- **Matches**: View and filter all matches
- **Teams**: Explore team statistics and performance
- **Model Status**: Check ML model training status and sync data

### 3. API Endpoints

The backend API is accessible at `http://localhost:5000/api` with the following key endpoints:

- `GET /api/teams` - List all teams
- `GET /api/matches` - List matches with filters
- `GET /api/predictions` - Get predictions
- `POST /api/predictions/{match_id}` - Generate prediction for a match
- `GET /api/upcoming-predictions` - Get predictions for upcoming matches
- `POST /api/model/train` - Train the prediction model

### 4. Initial Setup Tasks

When first accessing the application:

1. **Sync Teams and Competitions**:
   - Navigate to the Model Status page
   - Click "Sync Data" to fetch teams and competitions from the API

2. **Train the Model**:
   - On the Model Status page
   - Click "Train Model" (requires historical match data)

### 5. Server Management Commands

#### Start Backend Server (if not running):
```bash
cd /workspace/football-prediction-app/backend
source venv/bin/activate
python -m flask run --host=0.0.0.0 --port=5000
```

#### Start Frontend Server (if not running):
```bash
cd /workspace/football-prediction-app/frontend
npm start
```

#### Check Server Status:
```bash
# Check if backend is running
curl http://localhost:5000/

# Check if frontend is running
curl http://localhost:3000/
```

#### Stop Servers:
```bash
# Kill backend server
pkill -f "flask run"

# Kill frontend server
pkill -f "react-scripts"
```

### 6. Troubleshooting

#### Port Already in Use:
If you get a "port already in use" error:
```bash
# For backend (port 5000)
fuser -k 5000/tcp

# For frontend (port 3000)
fuser -k 3000/tcp
```

#### Backend Not Responding:
1. Check the logs:
   ```bash
   cd /workspace/football-prediction-app/backend
   cat flask_backend.log
   ```

2. Ensure virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

3. Reinstall dependencies if needed:
   ```bash
   pip install -r requirements_compatible.txt
   ```

#### Frontend Build Issues:
1. Clear npm cache:
   ```bash
   cd /workspace/football-prediction-app/frontend
   npm cache clean --force
   npm install
   ```

2. Check for TypeScript errors:
   ```bash
   npm run build
   ```

### 7. Development Notes

- The backend uses Flask's development server. For production, use Gunicorn or similar WSGI server
- The frontend is running in development mode with hot-reloading enabled
- API calls from frontend to backend are configured via the REACT_APP_API_URL environment variable
- The application includes CORS configuration for cross-origin requests

### 8. ML Model Information

The prediction model uses:
- **Features**: Team performance metrics, head-to-head records, recent form, injuries, fatigue
- **Algorithms**: Ensemble of XGBoost, LightGBM, Random Forest, and Gradient Boosting
- **Outputs**: Win/Draw/Loss probabilities, expected goals, confidence scores

### 9. API Key Configuration

The application is configured with a Football API key in the `.env` file. If you need to use a different API provider:

1. Edit `/workspace/football-prediction-app/backend/.env`
2. Update the `FOOTBALL_API_KEY` with your key
3. Restart the backend server

## Summary

The Football Prediction App is now fully set up and accessible. Both the backend (Flask) and frontend (React) servers are running, and you can access the application at http://localhost:3000. The ML dependencies have been configured to work with Python 3.13, ensuring compatibility with the latest features while maintaining support for the required machine learning libraries.