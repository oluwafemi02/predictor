# Football Prediction App

A comprehensive football match prediction system using machine learning, built with Flask (backend) and React (frontend).

## Features

- 🏆 **Match Predictions**: AI-powered predictions using XGBoost and LightGBM
- 📊 **Live Fixtures**: Real-time match data from SportMonks API
- 👥 **Team Management**: Browse teams and squad information
- 📈 **Betting Odds**: Integration with RapidAPI for odds data
- 🔄 **Background Sync**: Automated data updates via Celery
- 🚀 **Production Ready**: Deployed on Render with PostgreSQL and Redis

## Tech Stack

### Backend
- **Framework**: Flask 3.0
- **Database**: PostgreSQL with SQLAlchemy
- **Cache**: Redis
- **ML**: scikit-learn, XGBoost, LightGBM
- **Task Queue**: Celery
- **API Integration**: SportMonks, RapidAPI

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Data Fetching**: TanStack Query
- **Routing**: React Router v6

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd football-prediction-app

# Set up environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Install and run with Make
make setup       # Install dependencies
make dev         # Run backend
make frontend-dev # Run frontend (in another terminal)
```

Visit http://localhost:5173 to see the app.

## Documentation

- 📚 [Getting Started Guide](./DOCS/GETTING_STARTED.md) - Local development setup
- 🚀 [Deployment Guide](./DOCS/DEPLOYMENT_RENDER.md) - Deploy to Render
- 📡 [API Documentation](./DOCS/API_USAGE.md) - API endpoints and examples
- 🏗️ [Architecture Overview](./DOCS/ARCHITECTURE_AUDIT.md) - System design and improvements

## Project Structure

```
football-prediction-app/
├── backend/
│   ├── app.py              # Flask application factory
│   ├── models.py           # Database models
│   ├── api_routes.py       # API endpoints
│   ├── utils/              # Utilities (HTTP client, cache)
│   └── tests/              # Backend tests
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   └── lib/            # API client
│   └── public/             # Static assets
├── DOCS/                   # Documentation
└── .github/workflows/      # CI/CD pipelines
```

## Key Improvements Made

### ✅ Fixed Issues
- Fixed ImportError for `handle_api_errors` and `log_performance`
- Resolved CORS configuration warnings
- Added `/healthz` endpoint for health checks

### 🔧 Backend Enhancements
- Added resilient HTTP client with retry logic and circuit breakers
- Implemented caching utilities with Redis
- Created comprehensive error handling
- Added `/api/version` endpoint

### 🎨 Frontend Redesign
- Migrated to Vite + React + TypeScript
- Implemented clean, minimal UI with Tailwind CSS
- Added proper loading, error, and empty states
- Created responsive navigation

### 📝 Documentation
- Comprehensive getting started guide
- Detailed Render deployment instructions
- API usage documentation with examples

### 🔄 CI/CD
- GitHub Actions workflow for testing
- Docker support for containerization
- Security scanning with Trivy

## API Examples

### Get Fixtures
```bash
curl "http://localhost:5000/api/v1/fixtures?date_from=2025-01-01&date_to=2025-01-07"
```

### Get Predictions
```bash
curl "http://localhost:5000/api/v1/predictions?min_confidence=80"
```

See [API Documentation](./DOCS/API_USAGE.md) for more examples.

## Environment Variables

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SPORTMONKS_API_KEY` - SportMonks API key
- `SECRET_KEY` - Flask secret key

### Optional
- `RAPIDAPI_KEY` - For odds data
- `ENABLE_SCHEDULER` - Enable background sync
- `CORS_ORIGINS` - Allowed CORS origins

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov

# Frontend tests
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues or questions:
- Check the [documentation](./DOCS/)
- Review existing [GitHub issues]
- Contact the maintainers

---

Built with ❤️ for football prediction enthusiasts