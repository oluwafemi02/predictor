#!/bin/bash

# Football Prediction App - Backend Build Script
# This script prepares the backend for deployment

echo "Starting backend build process..."

# Exit on error
set -e

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate || . .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    flask db upgrade
fi

# Collect static files if needed
if [ -d "static" ]; then
    echo "Static files directory found"
fi

# Run tests if in CI/CD environment
if [ "$RUN_TESTS" = "true" ]; then
    echo "Running tests..."
    pytest tests/ -v
fi

# Check for required environment variables in production
if [ "$FLASK_ENV" = "production" ]; then
    echo "Checking production environment variables..."
    required_vars=("SECRET_KEY" "DATABASE_URL" "TOKEN_ENCRYPTION_PASSWORD" "TOKEN_ENCRYPTION_SALT")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "ERROR: Required environment variable $var is not set!"
            exit 1
        fi
    done
    
    echo "All required environment variables are set."
fi

echo "Build process completed successfully!"

# Create a marker file to indicate successful build
touch .build-success

exit 0