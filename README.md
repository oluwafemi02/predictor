# ⚽ Football Match Prediction App

A comprehensive web application that predicts football match outcomes using machine learning, real-time data integration, and advanced analytics.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- Redis (for caching)
- PostgreSQL (for production)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd football-prediction-app
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your secrets
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python init_db.py

# Run the server
python app.py
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

The app will be available at http://localhost:3000

## 📋 Features

### Core Functionality
- **Match Predictions**: ML-powered predictions with win/draw/loss probabilities
- **Live Data**: Real-time integration with SportMonks API
- **Team Analytics**: Comprehensive team statistics and performance metrics
- **Player Tracking**: Injury reports and player performance data
- **League Tables**: Up-to-date standings and fixtures
- **Historical Analysis**: Head-to-head records and form analysis

### Technical Features
- **Ensemble ML Model**: Combines XGBoost, LightGBM, Random Forest, and Gradient Boosting
- **Caching**: Redis-based caching for improved performance
- **Responsive UI**: Modern React interface with Material-UI
- **API Security**: Token-based authentication with encryption
- **Automated Sync**: Scheduled data updates every 6 hours

## 🏗️ Architecture

```
football-prediction-app/
├── backend/                 # Flask API server
│   ├── app.py              # Main application entry
│   ├── models.py           # Database models
│   ├── config.py           # Configuration
│   ├── sportmonks_routes.py  # SportMonks API integration
│   ├── prediction_engine.py   # ML prediction logic
│   └── requirements.txt    # Python dependencies
├── frontend/               # React application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service layer
│   │   └── App.tsx        # Main app component
│   └── package.json       # Node dependencies
└── render.yaml            # Deployment configuration
```

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```bash
# Security
SECRET_KEY=your-secret-key-here
TOKEN_ENCRYPTION_PASSWORD=strong-password
TOKEN_ENCRYPTION_SALT=unique-salt

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
SPORTMONKS_API_KEY=your-sportmonks-key
SPORTMONKS_FALLBACK_TOKENS=token1,token2,token3

# CORS
CORS_ORIGINS=http://localhost:3000,https://your-frontend-url.com
```

**Frontend (.env)**
```bash
REACT_APP_API_URL=http://localhost:5000
REACT_APP_SPORTMONKS_ENABLED=true
```

## 🔮 Prediction Model

### Features Used
- Team performance metrics (win rate, goals scored/conceded)
- Home/away specific statistics
- Recent form (last 5 matches)
- Head-to-head records
- Player injuries and availability
- Days since last match (fatigue factor)
- Advanced stats (possession, shots, pass accuracy)

### Model Output
- Win/Draw/Loss probabilities
- Expected goals for each team
- Over/Under 2.5 goals probability
- Both teams to score probability
- Confidence score
- Key prediction factors

## 📡 API Endpoints

### Public Endpoints
- `GET /api/teams` - List all teams
- `GET /api/matches` - List matches with filters
- `GET /api/fixtures` - Get upcoming fixtures
- `GET /api/leagues` - List available leagues

### Prediction Endpoints
- `GET /api/predictions/main` - Main page predictions
- `POST /api/predictions/generate` - Generate new prediction
- `GET /api/predictions/upcoming` - Upcoming match predictions
- `GET /api/predictions/accuracy` - Model accuracy stats

### SportMonks Integration
- `GET /api/sportmonks/sync/status` - Sync status
- `POST /api/sportmonks/sync/fixtures` - Sync fixtures
- `GET /api/sportmonks/fixtures/today` - Today's fixtures
- `GET /api/sportmonks/predictions/value-bets` - Value bet analysis

## 🚀 Deployment

### Using Render (Recommended)

1. **Fork this repository**

2. **Create Render account** at https://render.com

3. **Deploy using render.yaml**
   - Connect your GitHub repository
   - Render will automatically detect render.yaml
   - Set environment variables in Render dashboard

4. **Set up services**
   - Backend API (Web Service)
   - Frontend (Static Site)
   - Redis (Cache)
   - PostgreSQL (Database)
   - Scheduler (Background Worker)

### Manual Deployment

See [deployment guide](docs/deployment.md) for detailed instructions.

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### API Testing
```bash
# Test endpoints
./test_endpoints.sh

# Performance testing
python test_api_performance.py
```

## 🔒 Security

- All sensitive data stored in environment variables
- API authentication using encrypted tokens
- CORS properly configured
- SQL injection protection via SQLAlchemy ORM
- Input validation on all endpoints
- Rate limiting on API endpoints

## 📊 Monitoring

The application includes built-in monitoring for:
- API response times
- Prediction accuracy tracking
- Cache hit rates
- Error logging and alerts
- Database query performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This application is for educational and entertainment purposes only. Predictions are based on statistical analysis and should not be used as the sole basis for betting decisions. Please gamble responsibly.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the `/docs` folder
- **API Issues**: Verify API keys and rate limits

---

**Last Updated**: August 2025
