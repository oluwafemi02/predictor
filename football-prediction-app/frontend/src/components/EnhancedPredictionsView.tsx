import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Row, Col, ProgressBar, Button, Form, Alert, ListGroup, Nav, Tab } from 'react-bootstrap';
import { 
  Brain, Calendar, TrendingUp, Target, DollarSign, AlertCircle, 
  Award, Trophy, Shield, Activity, Users, Info, ChevronRight,
  Star, TrendingDown, BarChart3
} from 'lucide-react';
import axios from 'axios';
import './EnhancedPredictionsView.css';

interface EnhancedPrediction {
  fixture_id: number;
  home_team: string;
  away_team: string;
  date: string;
  win_probability_home: number;
  win_probability_away: number;
  draw_probability: number;
  confidence_level: 'high' | 'medium' | 'low';
  prediction_factors: {
    form_impact?: number;
    h2h_pattern?: string;
    injury_impact?: number;
    motivation?: string;
  };
  prediction_summary: string;
  recommended_bets: Array<{
    type: string;
    selection: string;
    probability: number;
    confidence: string;
    reasoning: string;
  }>;
  expected_goals: {
    home: number;
    away: number;
  };
  btts_probability: number;
  over_25_probability: number;
  league?: string;
}

interface ValueBet {
  fixture_id: number;
  home_team: string;
  away_team: string;
  date: string;
  bet_type: string;
  team?: string;
  probability: number;
  confidence_level: string;
  expected_goals?: {
    home: number;
    away: number;
  };
  recommended_bets?: Array<{
    type: string;
    selection: string;
    probability: number;
    confidence: string;
    reasoning: string;
  }>;
  summary?: string;
  league?: string;
}

const EnhancedPredictionsView: React.FC = () => {
  const [predictions, setPredictions] = useState<EnhancedPrediction[]>([]);
  const [valueBets, setValueBets] = useState<ValueBet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDays, setSelectedDays] = useState(7);
  const [selectedLeague, setSelectedLeague] = useState<string>('');
  const [minConfidence, setMinConfidence] = useState<'low' | 'medium' | 'high'>('low');
  const [activeTab, setActiveTab] = useState<'predictions' | 'valuebets'>('predictions');

  const fetchEnhancedPredictions = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        date_from: new Date().toISOString().split('T')[0],
        date_to: new Date(Date.now() + selectedDays * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        min_confidence: minConfidence
      });
      
      if (selectedLeague) {
        params.append('league_id', selectedLeague);
      }

      // Fetch enhanced predictions
      const predictionsResponse = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/v1/predictions/enhanced?${params}`,
        {
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );
      
      if (predictionsResponse.data && predictionsResponse.data.predictions) {
        setPredictions(predictionsResponse.data.predictions);
      }

      // Fetch value bets
      const valueBetsResponse = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/v1/predictions/value-bets?${params}`,
        {
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );
      
      if (valueBetsResponse.data && valueBetsResponse.data.value_bets) {
        setValueBets(valueBetsResponse.data.value_bets);
      }
    } catch (err: any) {
      console.error('Error fetching enhanced predictions:', err);
      setError('Failed to fetch enhanced predictions. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnhancedPredictions();
  }, [selectedDays, selectedLeague, minConfidence]);

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return <Badge bg="success"><Trophy size={14} className="me-1" />High Confidence</Badge>;
      case 'medium':
        return <Badge bg="warning"><Shield size={14} className="me-1" />Medium Confidence</Badge>;
      default:
        return <Badge bg="secondary"><Info size={14} className="me-1" />Low Confidence</Badge>;
    }
  };

  const getProbabilityColor = (probability: number): string => {
    if (probability >= 70) return 'success';
    if (probability >= 55) return 'warning';
    return 'danger';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const renderPredictionCard = (prediction: EnhancedPrediction) => {
    const maxProb = Math.max(
      prediction.win_probability_home,
      prediction.win_probability_away,
      prediction.draw_probability
    );
    
    let predictedOutcome = '';
    let outcomeColor = '';
    if (prediction.win_probability_home === maxProb) {
      predictedOutcome = `${prediction.home_team} Win`;
      outcomeColor = 'primary';
    } else if (prediction.win_probability_away === maxProb) {
      predictedOutcome = `${prediction.away_team} Win`;
      outcomeColor = 'info';
    } else {
      predictedOutcome = 'Draw';
      outcomeColor = 'warning';
    }

    return (
      <Col key={prediction.fixture_id} xl={6} className="mb-4">
        <Card className="enhanced-prediction-card h-100 shadow">
          <Card.Header className="d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-1">{prediction.home_team} vs {prediction.away_team}</h5>
              <small className="text-muted">{formatDate(prediction.date)}</small>
              {prediction.league && <Badge bg="secondary" className="ms-2">{prediction.league}</Badge>}
            </div>
            {getConfidenceBadge(prediction.confidence_level)}
          </Card.Header>
          
          <Card.Body>
            {/* Main Prediction */}
            <div className="prediction-outcome mb-3 p-3 rounded bg-light">
              <h6 className="mb-2 d-flex align-items-center">
                <Brain size={18} className="me-2 text-primary" />
                AI Prediction: <Badge bg={outcomeColor} className="ms-2">{predictedOutcome}</Badge>
              </h6>
              <p className="mb-0 text-muted small">{prediction.prediction_summary}</p>
            </div>

            {/* Probabilities */}
            <div className="probabilities-section mb-3">
              <h6 className="mb-2">Match Outcome Probabilities</h6>
              <div className="mb-2">
                <div className="d-flex justify-content-between mb-1">
                  <span>{prediction.home_team} Win</span>
                  <span className="fw-bold">{prediction.win_probability_home}%</span>
                </div>
                <ProgressBar 
                  now={prediction.win_probability_home} 
                  variant={getProbabilityColor(prediction.win_probability_home)}
                />
              </div>
              <div className="mb-2">
                <div className="d-flex justify-content-between mb-1">
                  <span>Draw</span>
                  <span className="fw-bold">{prediction.draw_probability}%</span>
                </div>
                <ProgressBar 
                  now={prediction.draw_probability} 
                  variant={getProbabilityColor(prediction.draw_probability)}
                />
              </div>
              <div className="mb-2">
                <div className="d-flex justify-content-between mb-1">
                  <span>{prediction.away_team} Win</span>
                  <span className="fw-bold">{prediction.win_probability_away}%</span>
                </div>
                <ProgressBar 
                  now={prediction.win_probability_away} 
                  variant={getProbabilityColor(prediction.win_probability_away)}
                />
              </div>
            </div>

            {/* Goals Predictions */}
            <Row className="mb-3">
              <Col md={6}>
                <div className="stat-box p-2 border rounded text-center">
                  <Activity size={20} className="text-primary mb-1" />
                  <div className="small text-muted">Expected Goals</div>
                  <div className="fw-bold">
                    {prediction.expected_goals.home.toFixed(1)} - {prediction.expected_goals.away.toFixed(1)}
                  </div>
                </div>
              </Col>
              <Col md={6}>
                <div className="stat-box p-2 border rounded text-center">
                  <Target size={20} className="text-success mb-1" />
                  <div className="small text-muted">Over 2.5 Goals</div>
                  <div className="fw-bold">{prediction.over_25_probability}%</div>
                </div>
              </Col>
            </Row>

            {/* Recommended Bets */}
            {prediction.recommended_bets.length > 0 && (
              <div className="recommended-bets">
                <h6 className="mb-2 d-flex align-items-center">
                  <Star size={18} className="me-2 text-warning" />
                  Recommended Bets
                </h6>
                <ListGroup variant="flush">
                  {prediction.recommended_bets.slice(0, 3).map((bet, index) => (
                    <ListGroup.Item key={index} className="px-0 py-2">
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <Badge bg={bet.confidence === 'high' ? 'success' : 'warning'} className="me-2">
                            {bet.type}
                          </Badge>
                          <span className="fw-medium">{bet.selection}</span>
                          <div className="small text-muted mt-1">{bet.reasoning}</div>
                        </div>
                        <Badge bg="light" text="dark">{bet.probability}%</Badge>
                      </div>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              </div>
            )}

            {/* Prediction Factors */}
            {Object.keys(prediction.prediction_factors).length > 0 && (
              <div className="prediction-factors mt-3 pt-3 border-top">
                <h6 className="mb-2 small text-muted">Key Factors</h6>
                <div className="d-flex flex-wrap gap-2">
                  {prediction.prediction_factors.form_impact !== undefined && (
                    <Badge bg="light" text="dark">
                      Form Impact: {prediction.prediction_factors.form_impact > 0 ? '+' : ''}{prediction.prediction_factors.form_impact.toFixed(1)}
                    </Badge>
                  )}
                  {prediction.prediction_factors.h2h_pattern && (
                    <Badge bg="light" text="dark">
                      H2H: {prediction.prediction_factors.h2h_pattern}
                    </Badge>
                  )}
                  {prediction.prediction_factors.motivation && (
                    <Badge bg="light" text="dark">
                      {prediction.prediction_factors.motivation}
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </Card.Body>
        </Card>
      </Col>
    );
  };

  const renderValueBetCard = (bet: ValueBet) => {
    return (
      <Col key={`${bet.fixture_id}-${bet.bet_type}`} lg={4} md={6} className="mb-3">
        <Card className="value-bet-card h-100 shadow-sm">
          <Card.Body>
            <div className="d-flex justify-content-between align-items-start mb-2">
              <h6 className="mb-0">{bet.home_team} vs {bet.away_team}</h6>
              {getConfidenceBadge(bet.confidence_level)}
            </div>
            
            <div className="mb-2">
              <small className="text-muted">{formatDate(bet.date)}</small>
              {bet.league && <Badge bg="secondary" className="ms-2 small">{bet.league}</Badge>}
            </div>

            <div className="bet-recommendation p-3 rounded bg-light mb-2">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <Badge bg="primary" className="mb-1">{bet.bet_type}</Badge>
                  {bet.team && bet.team !== 'Draw' && (
                    <div className="fw-bold">{bet.team}</div>
                  )}
                </div>
                <div className="text-end">
                  <div className="h4 mb-0 text-success">{bet.probability}%</div>
                  <small className="text-muted">Probability</small>
                </div>
              </div>
            </div>

            {bet.expected_goals && (
              <div className="small text-muted">
                Expected Score: {bet.expected_goals.home.toFixed(1)} - {bet.expected_goals.away.toFixed(1)}
              </div>
            )}

            {bet.summary && (
              <p className="small text-muted mt-2 mb-0">{bet.summary}</p>
            )}
          </Card.Body>
        </Card>
      </Col>
    );
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Analyzing fixtures with AI...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger" className="m-3">
        <AlertCircle size={20} className="me-2" />
        {error}
      </Alert>
    );
  }

  return (
    <div className="enhanced-predictions-container">
      {/* Header */}
      <div className="header-section mb-4">
        <h2 className="d-flex align-items-center">
          <Brain size={28} className="me-2 text-primary" />
          AI-Powered Football Predictions
        </h2>
        <p className="text-muted">
          Advanced predictions using team form, head-to-head history, injuries, and multiple data factors
        </p>
      </div>

      {/* Filters */}
      <Card className="filter-card mb-4">
        <Card.Body>
          <Row>
            <Col md={4}>
              <Form.Group>
                <Form.Label>Time Period</Form.Label>
                <Form.Select 
                  value={selectedDays} 
                  onChange={(e) => setSelectedDays(Number(e.target.value))}
                >
                  <option value={1}>Next 24 Hours</option>
                  <option value={3}>Next 3 Days</option>
                  <option value={7}>Next 7 Days</option>
                  <option value={14}>Next 14 Days</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={4}>
              <Form.Group>
                <Form.Label>League</Form.Label>
                <Form.Select 
                  value={selectedLeague} 
                  onChange={(e) => setSelectedLeague(e.target.value)}
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
            <Col md={4}>
              <Form.Group>
                <Form.Label>Minimum Confidence</Form.Label>
                <Form.Select 
                  value={minConfidence} 
                  onChange={(e) => setMinConfidence(e.target.value as 'low' | 'medium' | 'high')}
                >
                  <option value="low">All Predictions</option>
                  <option value="medium">Medium & High</option>
                  <option value="high">High Only</option>
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Tab Navigation */}
      <Tab.Container activeKey={activeTab} onSelect={(k) => setActiveTab(k as 'predictions' | 'valuebets')}>
        <Nav variant="pills" className="mb-4">
          <Nav.Item>
            <Nav.Link eventKey="predictions">
              <BarChart3 size={18} className="me-2" />
              All Predictions ({predictions.length})
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="valuebets">
              <Trophy size={18} className="me-2" />
              Value Bets ({valueBets.length})
            </Nav.Link>
          </Nav.Item>
        </Nav>

        <Tab.Content>
          {/* All Predictions Tab */}
          <Tab.Pane eventKey="predictions">
            {predictions.length === 0 ? (
              <Alert variant="info">
                <Info size={20} className="me-2" />
                No predictions available for the selected criteria.
              </Alert>
            ) : (
              <Row>
                {predictions.map(renderPredictionCard)}
              </Row>
            )}
          </Tab.Pane>

          {/* Value Bets Tab */}
          <Tab.Pane eventKey="valuebets">
            {valueBets.length === 0 ? (
              <Alert variant="info">
                <Info size={20} className="me-2" />
                No high-confidence value bets found for the selected period.
              </Alert>
            ) : (
              <>
                <Alert variant="success" className="mb-4">
                  <Star size={20} className="me-2" />
                  <strong>Value Bets:</strong> These are predictions with probability &gt;60% offering the best betting value.
                </Alert>
                <Row>
                  {valueBets.map(renderValueBetCard)}
                </Row>
              </>
            )}
          </Tab.Pane>
        </Tab.Content>
      </Tab.Container>
    </div>
  );
};

export default EnhancedPredictionsView;