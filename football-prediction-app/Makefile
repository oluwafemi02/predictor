# Football Prediction App Makefile

.PHONY: help dev test lint format clean setup db-init db-migrate frontend-dev build deploy

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup        - Install all dependencies"
	@echo "  make dev          - Run backend development server"
	@echo "  make frontend-dev - Run frontend development server"
	@echo "  make test         - Run all tests with coverage"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code automatically"
	@echo "  make db-init      - Initialize database"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make clean        - Clean cache and temporary files"
	@echo "  make build        - Build production assets"
	@echo "  make deploy       - Deploy to Render"

# Setup development environment
setup:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
	@echo "✅ Setup complete!"

# Run backend development server
dev:
	cd backend && flask run --debug --host=0.0.0.0 --port=5000

# Run frontend development server
frontend-dev:
	cd frontend && npm start

# Run tests with coverage
test:
	cd backend && pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Run linting
lint:
	cd backend && ruff check . || true
	cd backend && pylint *.py --disable=all --enable=E,F || true
	cd frontend && npm run lint || true

# Format code
format:
	cd backend && black . || true
	cd backend && isort . || true
	cd frontend && npm run format || true

# Initialize database
db-init:
	cd backend && flask db init
	cd backend && flask db migrate -m "Initial migration"
	cd backend && flask db upgrade

# Run database migrations
db-migrate:
	cd backend && flask db migrate -m "Auto migration"
	cd backend && flask db upgrade

# Clean cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf backend/htmlcov
	rm -rf backend/.pytest_cache
	rm -rf frontend/build
	rm -rf frontend/node_modules/.cache

# Build production assets
build:
	cd frontend && npm run build
	@echo "✅ Frontend build complete!"

# Deploy to Render (requires Render CLI)
deploy:
	@echo "Deploying to Render..."
	@echo "Make sure you have committed all changes and pushed to your repository"
	@echo "Render will automatically deploy from your GitHub repository"

# Run background worker
worker:
	cd backend && celery -A celery_app worker --loglevel=info

# Run scheduler
scheduler:
	cd backend && python run_scheduler.py

# Run Redis (requires Docker)
redis:
	docker run -d -p 6379:6379 redis:alpine

# Run PostgreSQL (requires Docker)
postgres:
	docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:alpine

# Seed database with sample data
seed:
	cd backend && python populate_data.py

# Check environment variables
check-env:
	@echo "Checking required environment variables..."
	@test -n "${DATABASE_URL}" || echo "❌ DATABASE_URL is not set"
	@test -n "${REDIS_URL}" || echo "❌ REDIS_URL is not set"
	@test -n "${SPORTMONKS_API_KEY}" || echo "❌ SPORTMONKS_API_KEY is not set"
	@test -n "${RAPIDAPI_KEY}" || echo "⚠️  RAPIDAPI_KEY is not set (required for odds)"
	@test -n "${SECRET_KEY}" || echo "❌ SECRET_KEY is not set"
	@echo "✅ Environment check complete!"