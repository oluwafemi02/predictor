# Football Match Prediction App

A comprehensive web-based application that predicts football match outcomes using machine learning. The app analyzes team performance, player statistics, injuries, historical data, and various other factors to provide accurate predictions.

## Features

- **Match Predictions**: Accurate predictions for upcoming football matches with probability distributions
- **Live Data Integration**: Fetches real-time data from football APIs
- **Machine Learning Models**: Ensemble of XGBoost, LightGBM, Random Forest, and Gradient Boosting
- **Comprehensive Analysis**: Considers team form, head-to-head records, injuries, and performance metrics
- **Beautiful UI**: Modern, responsive interface built with React and Material-UI
- **Real-time Updates**: Automatic data synchronization and prediction updates
- **Statistical Insights**: Detailed team statistics, league tables, and performance analytics

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **ML Libraries**: scikit-learn, XGBoost, LightGBM
- **Task Queue**: Celery with Redis
- **API Integration**: Multiple football data providers

### Frontend
- **Framework**: React with TypeScript
- **UI Library**: Material-UI (MUI)
- **State Management**: React Query
- **Routing**: React Router v6
- **Charts**: Recharts
- **Date Handling**: date-fns

## Installation

### Prerequisites
- Python 3.8+
- Node.js 14+
- Redis (optional, for background tasks)
- PostgreSQL (optional, for production)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the Flask server:
```bash
python app.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env
```

4. Start the development server:
```bash
npm start
```

## Configuration

### API Keys

The app supports multiple football data providers. You'll need to obtain API keys from at least one:

1. **Football-Data.org** (Free tier available)
   - Sign up at https://www.football-data.org/
   - Add key to `FOOTBALL_API_KEY` in `.env`

2. **API-Football** (via RapidAPI)
   - Sign up at https://rapidapi.com/api-sports/api/api-football/
   - More comprehensive data but requires subscription

3. **TheSportsDB** (Free)
   - No API key required for basic usage
   - Limited to historical data

### Database Configuration

For production, use PostgreSQL:
```
DATABASE_URL=postgresql://username:password@localhost:5432/football_predictions
```

## Usage

### 1. Initial Setup

After installation, you need to:

1. **Sync Teams and Competitions**:
   - Go to Model Status page
   - Click "Sync Data" to fetch teams and competitions

2. **Train the Model**:
   - Navigate to Model Status
   - Click "Train Model" (requires historical match data)

### 2. Making Predictions

- **Dashboard**: View upcoming predictions and recent results
- **Predictions**: Browse all predictions with filtering options
- **Matches**: View and filter all matches
- **Teams**: Explore team statistics and performance

### 3. API Endpoints

Key endpoints:

- `GET /api/teams` - List all teams
- `GET /api/matches` - List matches with filters
- `GET /api/predictions` - Get predictions
- `POST /api/predictions/{match_id}` - Generate prediction for a match
- `GET /api/upcoming-predictions` - Get predictions for upcoming matches
- `POST /api/model/train` - Train the prediction model

## Model Details

The prediction model uses an ensemble approach with multiple algorithms:

### Features Used
- Team win/draw/loss rates
- Goals scored/conceded per match
- Home/away specific performance
- Recent form (last 5 matches)
- Head-to-head statistics
- Player injuries impact
- Days since last match (fatigue)
- Advanced stats (possession, shots, pass accuracy)

### Prediction Outputs
- Win/Draw/Loss probabilities
- Expected goals for each team
- Over/Under 2.5 goals probability
- Both teams to score probability
- Confidence score
- Key factors influencing the prediction

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Structure

```
football-prediction-app/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── config.py           # Configuration
│   ├── data_collector.py   # API data fetching
│   ├── prediction_model.py # ML model implementation
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── App.tsx         # Main app component
│   └── package.json        # Node dependencies
└── README.md
```

## Deployment

### Docker Deployment

```dockerfile
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment

1. Set up a production server (Ubuntu/Debian recommended)
2. Install Python, Node.js, PostgreSQL, Redis, and Nginx
3. Configure Nginx as reverse proxy
4. Use Gunicorn for Flask
5. Build React app: `npm run build`
6. Serve static files with Nginx

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Football data providers for APIs
- Open source ML libraries
- React and Material-UI communities

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review API provider documentation

---

**Note**: This app is for educational and entertainment purposes. Always gamble responsibly if using predictions for betting.

---

**Last Updated**: December 2024 - Added smooth transitions and improved scrollbar styling for better user experience.
