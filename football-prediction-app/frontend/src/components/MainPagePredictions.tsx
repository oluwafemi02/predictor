import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Badge, ProgressBar, Spinner, Alert, Button, Nav, Tab } from 'react-bootstrap';
import { FaTrophy, FaChartLine, FaExclamationTriangle, FaInfoCircle, FaClock, FaStar } from 'react-icons/fa';
import axios from '../services/api';
import './MainPagePredictions.css';

interface Prediction {
  fixture_id: number;
  home_team: string;
  away_team: string;
  date: string;
  main_prediction: string;
  main_probability: number;
  win_probability_home: number;
  win_probability_away: number;
  draw_probability: number;
  btts_probability: number;
  over_25_probability: number;
  confidence_level: 'high' | 'medium' | 'low';
  prediction_summary: string;
  top_value_bet?: {
    type: string;
    probability: number;
    confidence: string;
    recommended_stake: number;
  };
}

interface FeaturedPrediction {
  fixture_id: number;
  home_team: string;
  away_team: string;
  date: string;
  prediction_type: string;
  predicted_team?: string;
  probability: number;
  confidence_score: number;
  confidence_level: 'high' | 'medium' | 'low';
  prediction_summary: string;
  value_bets: Array<{
    type: string;
    probability: number;
    confidence: string;
    recommended_stake: number;
  }>;
  data_completeness: number;
}

const MainPagePredictions: React.FC = () => {
  const [todaysPredictions, setTodaysPredictions] = useState<Prediction[]>([]);
  const [featuredPredictions, setFeaturedPredictions] = useState<FeaturedPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('today');

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch today's predictions
      const todayResponse = await axios.get('/api/v1/predictions/today', {
        params: { limit: 15 }
      });
      setTodaysPredictions(todayResponse.data.predictions || []);

      // Fetch featured predictions
      const featuredResponse = await axios.get('/api/v1/predictions/featured', {
        params: { days: 3, min_confidence: 75 }
      });
      setFeaturedPredictions(featuredResponse.data.featured_predictions || []);
    } catch (err: any) {
      console.error('Error fetching predictions:', err);
      setError('Failed to load predictions. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceBadge = (level: string) => {
    const badges: Record<string, { variant: string; icon: JSX.Element }> = {
      high: { variant: 'success', icon: <FaStar /> },
      medium: { variant: 'warning', icon: <FaChartLine /> },
      low: { variant: 'secondary', icon: <FaInfoCircle /> }
    };
    
    const badge = badges[level] || badges.low;
    
    return (
      <Badge bg={badge.variant} className="confidence-badge">
        {badge.icon} {level.toUpperCase()}
      </Badge>
    );
  };

  const getProbabilityColor = (probability: number): string => {
    if (probability >= 70) return 'success';
    if (probability >= 50) return 'warning';
    return 'danger';
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
      return `Today, ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return `Tomorrow, ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
    }
    
    return date.toLocaleString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const renderTodaysPrediction = (prediction: Prediction) => (
    <Col key={prediction.fixture_id} lg={6} xl={4} className="mb-4">
      <Card className="prediction-card h-100">
        <Card.Header className="prediction-header">
          <div className="d-flex justify-content-between align-items-center">
            <small className="text-muted">
              <FaClock /> {formatDate(prediction.date)}
            </small>
            {getConfidenceBadge(prediction.confidence_level)}
          </div>
        </Card.Header>
        
        <Card.Body>
          <div className="match-teams text-center mb-3">
            <h5 className="mb-1">{prediction.home_team}</h5>
            <span className="vs-text">vs</span>
            <h5 className="mt-1">{prediction.away_team}</h5>
          </div>
          
          <div className="main-prediction text-center mb-3">
            <Badge bg="primary" className="main-prediction-badge">
              <FaTrophy /> {prediction.main_prediction} ({prediction.main_probability}%)
            </Badge>
          </div>
          
          <div className="probability-bars mb-3">
            <div className="prob-item">
              <div className="d-flex justify-content-between">
                <small>Home Win</small>
                <small>{prediction.win_probability_home}%</small>
              </div>
              <ProgressBar 
                now={prediction.win_probability_home} 
                variant={getProbabilityColor(prediction.win_probability_home)}
                className="mb-2"
              />
            </div>
            
            <div className="prob-item">
              <div className="d-flex justify-content-between">
                <small>Draw</small>
                <small>{prediction.draw_probability}%</small>
              </div>
              <ProgressBar 
                now={prediction.draw_probability} 
                variant={getProbabilityColor(prediction.draw_probability)}
                className="mb-2"
              />
            </div>
            
            <div className="prob-item">
              <div className="d-flex justify-content-between">
                <small>Away Win</small>
                <small>{prediction.win_probability_away}%</small>
              </div>
              <ProgressBar 
                now={prediction.win_probability_away} 
                variant={getProbabilityColor(prediction.win_probability_away)}
                className="mb-2"
              />
            </div>
          </div>
          
          <div className="additional-markets">
            <Row>
              <Col xs={6}>
                <div className="market-stat">
                  <small className="text-muted">Over 2.5</small>
                  <div className="stat-value">{prediction.over_25_probability}%</div>
                </div>
              </Col>
              <Col xs={6}>
                <div className="market-stat">
                  <small className="text-muted">BTTS</small>
                  <div className="stat-value">{prediction.btts_probability}%</div>
                </div>
              </Col>
            </Row>
          </div>
          
          {prediction.top_value_bet && (
            <div className="value-bet-section mt-3">
              <Alert variant="info" className="value-bet-alert">
                <small>
                  <strong>Best Bet:</strong> {prediction.top_value_bet.type} 
                  ({prediction.top_value_bet.probability}%) - 
                  Stake: {prediction.top_value_bet.recommended_stake} units
                </small>
              </Alert>
            </div>
          )}
        </Card.Body>
      </Card>
    </Col>
  );

  const renderFeaturedPrediction = (prediction: FeaturedPrediction) => (
    <Col key={prediction.fixture_id} lg={6} className="mb-4">
      <Card className="featured-prediction-card h-100">
        <Card.Header className="featured-header">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <FaStar className="text-warning" /> Featured Prediction
            </div>
            <div>
              {getConfidenceBadge(prediction.confidence_level)}
              <Badge bg="info" className="ms-2">
                {prediction.confidence_score}% Confidence
              </Badge>
            </div>
          </div>
        </Card.Header>
        
        <Card.Body>
          <div className="match-info mb-3">
            <h4 className="text-center">
              {prediction.home_team} vs {prediction.away_team}
            </h4>
            <p className="text-center text-muted">
              {formatDate(prediction.date)}
            </p>
          </div>
          
          <div className="featured-prediction-display text-center mb-4">
            <h3 className="prediction-type">{prediction.prediction_type}</h3>
            {prediction.predicted_team && (
              <h4 className="predicted-team">{prediction.predicted_team}</h4>
            )}
            <div className="probability-display">
              <span className="probability-value">{prediction.probability}%</span>
              <span className="probability-label">Probability</span>
            </div>
          </div>
          
          <div className="prediction-summary mb-3">
            <p className="text-muted small">{prediction.prediction_summary}</p>
          </div>
          
          {prediction.value_bets.length > 0 && (
            <div className="value-bets-section">
              <h6>Value Bets:</h6>
              {prediction.value_bets.map((bet, index) => (
                <Badge key={index} bg="success" className="me-2 mb-2">
                  {bet.type} ({bet.probability}%)
                </Badge>
              ))}
            </div>
          )}
          
          <div className="data-completeness mt-3">
            <small className="text-muted">
              Data Completeness: {prediction.data_completeness}%
            </small>
            <ProgressBar 
              now={prediction.data_completeness} 
              variant="info" 
              className="mt-1"
              style={{ height: '5px' }}
            />
          </div>
        </Card.Body>
      </Card>
    </Col>
  );

  if (loading) {
    return (
      <Container className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading predictions...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="py-5">
        <Alert variant="danger" onClose={() => setError(null)} dismissible>
          <FaExclamationTriangle /> {error}
        </Alert>
        <div className="text-center">
          <Button variant="primary" onClick={fetchPredictions}>
            Try Again
          </Button>
        </div>
      </Container>
    );
  }

  return (
    <Container className="main-page-predictions py-4">
      <h2 className="mb-4 text-center">
        <FaChartLine /> AI-Powered Football Predictions
      </h2>
      
      <Tab.Container activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'today')}>
        <Nav variant="pills" className="justify-content-center mb-4">
          <Nav.Item>
            <Nav.Link eventKey="today">
              Today's Matches ({todaysPredictions.length})
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="featured">
              Featured Predictions ({featuredPredictions.length})
            </Nav.Link>
          </Nav.Item>
        </Nav>
        
        <Tab.Content>
          <Tab.Pane eventKey="today">
            {todaysPredictions.length === 0 ? (
              <Alert variant="info" className="text-center">
                <FaInfoCircle /> No matches scheduled for today. Check back later!
              </Alert>
            ) : (
              <Row>
                {todaysPredictions.map(renderTodaysPrediction)}
              </Row>
            )}
          </Tab.Pane>
          
          <Tab.Pane eventKey="featured">
            {featuredPredictions.length === 0 ? (
              <Alert variant="info" className="text-center">
                <FaInfoCircle /> No high-confidence predictions available at the moment.
              </Alert>
            ) : (
              <Row>
                {featuredPredictions.map(renderFeaturedPrediction)}
              </Row>
            )}
          </Tab.Pane>
        </Tab.Content>
      </Tab.Container>
    </Container>
  );
};

export default MainPagePredictions;