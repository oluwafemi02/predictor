#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run database migrations if Flask-Migrate is being used
if [ -d "migrations" ]; then
    echo "Running database migrations..."
    flask db upgrade
else
    echo "No migrations directory found. Creating tables directly..."
    python -c "from app import app, db; app.app_context().push(); db.create_all()"
fi

echo "Build completed successfully!"