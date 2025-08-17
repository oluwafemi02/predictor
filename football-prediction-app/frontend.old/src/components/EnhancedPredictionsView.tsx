import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Badge, ProgressBar, Spinner, Alert, Button, Form, Tab, Tabs } from 'react-bootstrap';
import api from '../services/api';
import './EnhancedPredictionsView.css';

interface EnhancedPrediction {
  fixture_id: number;
  fixture: {
    home_team: string;
    away_team: string;
    date: string;
    league?: string;
  };
  prediction: {
    match_result: {
      home_win: number;
      draw: number;
      away_win: number;
    };
    goals: {
      home: number;
      away: number;
      total: number;
    };
    btts: number;
    over_25: number;
  };
  confidence: number;
  summary: string;
  recommended_bet?: {
    type: string;
    selection: string;
    probability: number;
  };
}

const EnhancedPredictionsView: React.FC = () => {
  const [predictions, setPredictions] = useState<EnhancedPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<number | null>(null);
  const [minConfidence, setMinConfidence] = useState(50);
  const [dateRange, setDateRange] = useState({
    from: new Date().toISOString().split('T')[0],
    to: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchEnhancedPredictions();
  }, [selectedLeague, minConfidence, dateRange]);

  const fetchEnhancedPredictions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      params.append('date_from', dateRange.from);
      params.append('date_to', dateRange.to);
      params.append('min_confidence', minConfidence.toString());
      
      if (selectedLeague) {
        params.append('league_id', selectedLeague.toString());
      }
      
      const response = await api.get(`/api/v1/predictions/enhanced/upcoming?${params.toString()}`);
      setPredictions(response.data.predictions || []);
    } catch (err) {
      console.error('Error fetching enhanced predictions:', err);
      setError('Failed to load enhanced predictions. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 80) return <Badge bg="success">Very High</Badge>;
    if (confidence >= 70) return <Badge bg="primary">High</Badge>;
    if (confidence >= 60) return <Badge bg="info">Medium</Badge>;
    if (confidence >= 50) return <Badge bg="warning">Low</Badge>;
    return <Badge bg="secondary">Very Low</Badge>;
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 70) return 'success';
    if (probability >= 60) return 'primary';
    if (probability >= 50) return 'info';
    if (probability >= 40) return 'warning';
    return 'danger';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getOutcomeIcon = (type: string) => {
    switch (type) {
      case 'home': return '🏠';
      case 'away': return '✈️';
      case 'draw': return '🤝';
      default: return '';
    }
  };

  const renderPredictionCard = (prediction: EnhancedPrediction) => {
    const { match_result, goals, btts, over_25 } = prediction.prediction;
    const maxProb = Math.max(match_result.home_win, match_result.draw, match_result.away_win);
    const predictedOutcome = match_result.home_win === maxProb ? 'home' : 
                           match_result.away_win === maxProb ? 'away' : 'draw';

    return (
      <Card key={prediction.fixture_id} className="enhanced-prediction-card mb-4 shadow">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <div>
            <h5 className="mb-1">
              {prediction.fixture.home_team} vs {prediction.fixture.away_team}
            </h5>
            <small className="text-muted">{formatDate(prediction.fixture.date)}</small>
            {prediction.fixture.league && (
              <Badge bg="secondary" className="ms-2">{prediction.fixture.league}</Badge>
            )}
          </div>
          <div className="text-end">
            {getConfidenceBadge(prediction.confidence)}
            <div className="confidence-score mt-1">
              {prediction.confidence.toFixed(0)}%
            </div>
          </div>
        </Card.Header>
        
        <Card.Body>
          {/* Match Result Prediction */}
          <div className="mb-4">
            <h6 className="mb-3">Match Result Prediction</h6>
            <Row>
              <Col xs={4}>
                <div className={`outcome-box ${predictedOutcome === 'home' ? 'predicted' : ''}`}>
                  <div className="outcome-icon">{getOutcomeIcon('home')}</div>
                  <div className="outcome-label">Home Win</div>
                  <ProgressBar 
                    now={match_result.home_win} 
                    label={`${match_result.home_win.toFixed(1)}%`}
                    variant={getProbabilityColor(match_result.home_win)}
                  />
                </div>
              </Col>
              <Col xs={4}>
                <div className={`outcome-box ${predictedOutcome === 'draw' ? 'predicted' : ''}`}>
                  <div className="outcome-icon">{getOutcomeIcon('draw')}</div>
                  <div className="outcome-label">Draw</div>
                  <ProgressBar 
                    now={match_result.draw} 
                    label={`${match_result.draw.toFixed(1)}%`}
                    variant={getProbabilityColor(match_result.draw)}
                  />
                </div>
              </Col>
              <Col xs={4}>
                <div className={`outcome-box ${predictedOutcome === 'away' ? 'predicted' : ''}`}>
                  <div className="outcome-icon">{getOutcomeIcon('away')}</div>
                  <div className="outcome-label">Away Win</div>
                  <ProgressBar 
                    now={match_result.away_win} 
                    label={`${match_result.away_win.toFixed(1)}%`}
                    variant={getProbabilityColor(match_result.away_win)}
                  />
                </div>
              </Col>
            </Row>
          </div>

          {/* Goals Prediction */}
          <div className="mb-4">
            <h6 className="mb-3">Goals Prediction</h6>
            <Row>
              <Col md={6}>
                <div className="goals-box">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span>Expected Goals</span>
                    <Badge bg="dark">{goals.total.toFixed(1)}</Badge>
                  </div>
                  <div className="score-prediction">
                    <span className="team-score">{goals.home.toFixed(1)}</span>
                    <span className="score-separator">-</span>
                    <span className="team-score">{goals.away.toFixed(1)}</span>
                  </div>
                </div>
              </Col>
              <Col md={6}>
                <div className="stat-row">
                  <span>Over 2.5 Goals</span>
                  <ProgressBar 
                    now={over_25} 
                    label={`${over_25.toFixed(0)}%`}
                    variant={getProbabilityColor(over_25)}
                  />
                </div>
                <div className="stat-row mt-2">
                  <span>Both Teams to Score</span>
                  <ProgressBar 
                    now={btts} 
                    label={`${btts.toFixed(0)}%`}
                    variant={getProbabilityColor(btts)}
                  />
                </div>
              </Col>
            </Row>
          </div>

          {/* AI Summary */}
          <div className="mb-3">
            <h6 className="mb-2">AI Analysis</h6>
            <p className="prediction-summary">{prediction.summary}</p>
          </div>

          {/* Recommended Bet */}
          {prediction.recommended_bet && (
            <div className="recommended-bet">
              <Badge bg="success" className="me-2">Best Bet</Badge>
              <strong>{prediction.recommended_bet.type}:</strong> {prediction.recommended_bet.selection}
              <Badge bg="light" text="dark" className="ms-2">
                {prediction.recommended_bet.probability.toFixed(1)}%
              </Badge>
            </div>
          )}
        </Card.Body>
      </Card>
    );
  };

  return (
    <div className="enhanced-predictions-container">
      {/* Filters */}
      <Card className="mb-4 filter-card">
        <Card.Body>
          <Row className="align-items-end">
            <Col md={3}>
              <Form.Group>
                <Form.Label>League</Form.Label>
                <Form.Select 
                  value={selectedLeague || ''} 
                  onChange={(e) => setSelectedLeague(e.target.value ? parseInt(e.target.value) : null)}
                >
                  <option value="">All Leagues</option>
                  <option value="8">Premier League</option>
                  <option value="564">La Liga</option>
                  <option value="82">Bundesliga</option>
                  <option value="384">Serie A</option>
                  <option value="301">Ligue 1</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group>
                <Form.Label>Min Confidence: {minConfidence}%</Form.Label>
                <Form.Range 
                  min="0" 
                  max="100" 
                  step="10"
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(parseInt(e.target.value))}
                />
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group>
                <Form.Label>From Date</Form.Label>
                <Form.Control 
                  type="date" 
                  value={dateRange.from}
                  onChange={(e) => setDateRange({...dateRange, from: e.target.value})}
                />
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group>
                <Form.Label>To Date</Form.Label>
                <Form.Control 
                  type="date" 
                  value={dateRange.to}
                  onChange={(e) => setDateRange({...dateRange, to: e.target.value})}
                />
              </Form.Group>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Content */}
      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
          <p className="mt-3">Loading enhanced predictions...</p>
        </div>
      ) : error ? (
        <Alert variant="danger">{error}</Alert>
      ) : predictions.length === 0 ? (
        <Alert variant="info">
          No predictions found matching your criteria. Try adjusting the filters.
        </Alert>
      ) : (
        <div>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5>Found {predictions.length} High-Confidence Predictions</h5>
            <Button variant="outline-primary" size="sm" onClick={fetchEnhancedPredictions}>
              Refresh
            </Button>
          </div>
          
          <Tabs defaultActiveKey="all" className="mb-4">
            <Tab eventKey="all" title={`All (${predictions.length})`}>
              {predictions.map(renderPredictionCard)}
            </Tab>
            <Tab eventKey="high-confidence" title={`High Confidence (${predictions.filter(p => p.confidence >= 70).length})`}>
              {predictions.filter(p => p.confidence >= 70).map(renderPredictionCard)}
            </Tab>
            <Tab eventKey="value-bets" title={`Value Bets (${predictions.filter(p => p.recommended_bet && p.recommended_bet.probability >= 65).length})`}>
              {predictions
                .filter(p => p.recommended_bet && p.recommended_bet.probability >= 65)
                .map(renderPredictionCard)}
            </Tab>
          </Tabs>
        </div>
      )}
    </div>
  );
};

export default EnhancedPredictionsView;