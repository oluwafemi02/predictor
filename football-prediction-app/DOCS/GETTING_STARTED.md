# Getting Started - Football Prediction App

This guide will help you set up the Football Prediction App for local development.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Redis 6 or higher
- Git

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd football-prediction-app
   ```

2. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   
   # Edit the files with your configuration
   ```

3. **Install dependencies and run**
   ```bash
   # Using the Makefile (recommended)
   make setup    # Install all dependencies
   make dev      # Run backend
   # In another terminal:
   make frontend-dev  # Run frontend
   ```

## Detailed Setup

### Backend Setup

1. **Create a virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database**
   ```bash
   # Create PostgreSQL database
   createdb football_predictions
   
   # Run migrations
   flask db upgrade
   
   # Seed with sample data (optional)
   python populate_data.py
   ```

4. **Configure environment variables**
   Create a `.env` file in the backend directory:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost/football_predictions
   
   # Redis
   REDIS_URL=redis://localhost:6379/0
   
   # API Keys
   SPORTMONKS_API_KEY=your_key_here
   RAPIDAPI_KEY=your_key_here  # Optional, for odds data
   
   # Security
   SECRET_KEY=your_secret_key_here
   
   # Flask
   FLASK_ENV=development
   FLASK_DEBUG=1
   ```

5. **Run the backend**
   ```bash
   flask run --debug
   ```
   The API will be available at http://localhost:5000

### Frontend Setup

1. **Install Node dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   Create a `.env` file in the frontend directory:
   ```env
   VITE_API_BASE_URL=http://localhost:5000
   ```

3. **Run the frontend**
   ```bash
   npm run dev
   ```
   The app will be available at http://localhost:5173

### Running Background Services

1. **Redis** (required for caching and Celery)
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:alpine
   
   # Or install locally and run
   redis-server
   ```

2. **Celery Worker** (for background tasks)
   ```bash
   cd backend
   celery -A celery_app worker --loglevel=info
   ```

3. **Scheduler** (for periodic data sync)
   ```bash
   cd backend
   python run_scheduler.py
   ```

## Development Workflow

### Using Make Commands

```bash
make help         # Show all available commands
make dev          # Run backend server
make frontend-dev # Run frontend server
make test         # Run tests
make lint         # Run linting
make format       # Format code
make db-migrate   # Create and run migrations
make clean        # Clean cache files
```

### API Endpoints

The main API endpoints are:

- `GET /api/health` - Health check
- `GET /api/version` - Version info
- `GET /api/v1/fixtures` - Get upcoming matches
- `GET /api/v1/predictions` - Get match predictions
- `GET /api/v1/teams` - Get teams list
- `GET /api/v1/teams/{id}/squad` - Get team squad

See [API_USAGE.md](./API_USAGE.md) for detailed API documentation.

### Database Migrations

```bash
# Create a new migration
cd backend
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migrations
flask db downgrade
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## Common Issues

### ImportError on startup
- Ensure you're in the virtual environment
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Database connection errors
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure database exists: `createdb football_predictions`

### CORS errors
- Check CORS_ORIGINS environment variable
- For local development, ensure frontend URL is in allowed origins

### Redis connection errors
- Verify Redis is running: `redis-cli ping`
- Check REDIS_URL in .env

## Project Structure

```
football-prediction-app/
├── backend/
│   ├── app.py              # Flask application factory
│   ├── wsgi.py             # WSGI entry point
│   ├── api_routes.py       # API endpoints
│   ├── models.py           # Database models
│   ├── requirements.txt    # Python dependencies
│   └── utils/              # Utility modules
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── lib/            # API client
│   └── package.json        # Node dependencies
├── DOCS/                   # Documentation
└── Makefile               # Development commands
```

## Next Steps

1. Explore the API documentation in [API_USAGE.md](./API_USAGE.md)
2. Read about deployment in [DEPLOYMENT_RENDER.md](./DEPLOYMENT_RENDER.md)
3. Check the architecture overview in [ARCHITECTURE_AUDIT.md](./ARCHITECTURE_AUDIT.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs in `backend/flask.log`
3. Check the GitHub issues