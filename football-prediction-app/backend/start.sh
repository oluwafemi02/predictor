#!/usr/bin/env bash
# Start script for Render deployment

# Create database tables if they don't exist
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"

# Start the application with gunicorn
exec gunicorn app:app --bind 0.0.0.0:$PORT