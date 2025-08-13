#!/usr/bin/env bash
# Start script for Render deployment

# Ensure we're in the right directory
cd /opt/render/project/src/football-prediction-app/backend || exit 1

# Create database tables if they don't exist
echo "Initializing database..."
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"

# Start the application with gunicorn
echo "Starting application..."
exec gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 120