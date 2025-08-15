import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Row, Col, ProgressBar, Button, Form } from 'react-bootstrap';
import { Brain, Calendar, TrendingUp, Target, DollarSign, AlertCircle } from 'lucide-react';
import axios from 'axios';
import './PredictionsView.css';
import OddsDisplay from './OddsDisplay';
import PredictionDetails from './PredictionDetails';

interface Prediction {
  id: number;
  fixture_id: number;
  date: string;
  status?: string;
  league: {
    id: number;
    name: string;
    logo: string;
  };
  home_team: {
    id: number;
    name: string;
    logo: string;
  };
  away_team: {
    id: number;
    name: string;
    logo: string;
  };
  scores?: any;
  predictions?: {
    match_winner?: {
      home_win: number;
      draw: number;
      away_win: number;
    };
    goals?: {
      over_15: number;
      under_15: number;
      over_25: number;
      under_25: number;
      over_35: number;
      under_35: number;
      over_45?: number;
      under_45?: number;
      btts_yes?: number;
      btts_no?: number;
    };
    btts?: {
      yes: number;
      no: number;
    };
    correct_scores?: Array<{
      score: string;
      probability: number;
    }>;
    double_chance?: {
      home_or_draw: number;
      away_or_draw: number;
      home_or_away: number;
    };
    first_half?: {
      home: number;
      draw: number;
      away: number;
    };
    corners?: {
      [key: string]: number;
    };
    team_goals?: {
      home: {
        [key: string]: number;
      };
      away: {
        [key: string]: number;
      };
    };
  };
  prediction_confidence?: string;
}

interface AllFixtures {
  past: Prediction[];
  today: Prediction[];
  upcoming: Prediction[];
}

const PredictionsView: React.FC = () => {
  const [allFixtures, setAllFixtures] = useState<AllFixtures>({ past: [], today: [], upcoming: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDays, setSelectedDays] = useState(7);
  const [selectedLeague, setSelectedLeague] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'past' | 'today' | 'upcoming'>('upcoming');

  const fetchPredictions = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        days_back: selectedDays.toString(),
        days_ahead: selectedDays.toString(),
        predictions: 'true',
      });
      
      if (selectedLeague) {
        params.append('league_id', selectedLeague);
      }

      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/sportmonks/fixtures/all?${params}`,
        {
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );
      
      if (response.data && response.data.fixtures) {
        setAllFixtures(response.data.fixtures);
      } else {
        setAllFixtures({ past: [], today: [], upcoming: [] });
        setError('No fixtures data received from server');
      }
    } catch (err: any) {
      console.error('Error fetching predictions:', err);
      let errorMessage = 'Failed to fetch predictions';
      
      if (err.response) {
        // Server responded with error
        errorMessage = err.response.data?.message || err.response.data?.error || `Server error: ${err.response.status}`;
      } else if (err.request) {
        // Request made but no response
        errorMessage = 'Unable to reach the server. Please check your connection.';
      } else {
        // Something else happened
        errorMessage = err.message || 'An unexpected error occurred';
      }
      
      setError(errorMessage);
      setAllFixtures({ past: [], today: [], upcoming: [] });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [selectedDays, selectedLeague]);

  const getWinnerPrediction = (pred: { home_win: number; draw: number; away_win: number }) => {
    const max = Math.max(pred.home_win, pred.draw, pred.away_win);
    if (max === pred.home_win) return { type: 'Home Win', prob: pred.home_win, variant: 'primary' };
    if (max === pred.draw) return { type: 'Draw', prob: pred.draw, variant: 'warning' };
    return { type: 'Away Win', prob: pred.away_win, variant: 'info' };
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 70) return 'success';
    if (probability >= 50) return 'warning';
    return 'danger';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading AI predictions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        <AlertCircle className="me-2" />
        <strong>Error:</strong> {error}
      </div>
    );
  }

  return (
    <div className="predictions-container">
      <div className="predictions-header mb-4">
        <Row className="align-items-center">
          <Col md={6}>
            <h3 className="mb-0">
              <Brain className="me-2" size={24} />
              AI Match Predictions
            </h3>
            <p className="text-muted mb-0">Powered by SportMonks Machine Learning</p>
          </Col>
          <Col md={6}>
            <Row>
              <Col sm={6}>
                <Form.Group>
                  <Form.Label className="small">Time Range</Form.Label>
                  <Form.Select 
                    value={selectedDays} 
                    onChange={(e) => setSelectedDays(Number(e.target.value))}
                    size="sm"
                  >
                    <option value={1}>1 day</option>
                    <option value={3}>3 days</option>
                    <option value={7}>7 days</option>
                    <option value={14}>14 days</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col sm={6}>
                <Form.Group>
                  <Form.Label className="small">League Filter</Form.Label>
                  <Form.Select 
                    value={selectedLeague} 
                    onChange={(e) => setSelectedLeague(e.target.value)}
                    size="sm"
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
            </Row>
          </Col>
        </Row>
      </div>

      <div className="fixtures-tabs mb-4">
        <ul className="nav nav-tabs">
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'past' ? 'active' : ''}`}
              onClick={() => setActiveTab('past')}
            >
              Past Fixtures ({allFixtures.past.length})
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'today' ? 'active' : ''}`}
              onClick={() => setActiveTab('today')}
            >
              Today's Fixtures ({allFixtures.today.length})
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'upcoming' ? 'active' : ''}`}
              onClick={() => setActiveTab('upcoming')}
            >
              Upcoming Fixtures ({allFixtures.upcoming.length})
            </button>
          </li>
        </ul>
      </div>

      {allFixtures[activeTab].length === 0 ? (
        <Card className="text-center py-5">
          <Card.Body>
            <Target size={48} className="text-muted mb-3" />
            <h5>No Predictions Available</h5>
            <p className="text-muted">Try adjusting your filters or check back later.</p>
          </Card.Body>
        </Card>
      ) : (
        <Row>
          {allFixtures[activeTab].map((prediction) => {
            const winner = prediction.predictions?.match_winner ? 
              getWinnerPrediction(prediction.predictions.match_winner) : null;
            const isPastFixture = activeTab === 'past';
            const hasScores = prediction.scores && prediction.scores.localteam_score !== undefined;
            
            return (
              <Col key={prediction.id} xl={6} className="mb-4">
                <Card className="prediction-card h-100 shadow-sm">
                  <Card.Header className="prediction-header">
                    <div className="d-flex justify-content-between align-items-center">
                      <div className="league-info">
                        {prediction.league.logo && (
                          <img 
                            src={prediction.league.logo} 
                            alt={prediction.league.name}
                            className="league-logo me-2"
                          />
                        )}
                        <span>{prediction.league.name}</span>
                      </div>
                      <div className="text-muted small">
                        <Calendar size={14} className="me-1" />
                        {formatDate(prediction.date)}
                        {prediction.status && prediction.status !== 'NS' && (
                          <Badge bg={isPastFixture ? 'secondary' : 'info'} className="ms-2">
                            {prediction.status}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </Card.Header>
                  <Card.Body>
                    <PredictionDetails 
                      predictions={prediction.predictions || {}}
                      confidence={prediction.prediction_confidence}
                      homeTeam={prediction.home_team.name}
                      awayTeam={prediction.away_team.name}
                    />

                    <div className="prediction-section mt-4">
                      <h6 className="section-title">
                        <DollarSign size={16} className="me-1" />
                        Live Odds
                      </h6>
                      <OddsDisplay fixtureId={prediction.id} showProbabilities={false} />
                    </div>
                  </Card.Body>

                  <Card.Footer className="prediction-footer">
                    <Button variant="outline-primary" size="sm" className="w-100">
                      <DollarSign size={16} className="me-1" />
                      View Value Bets
                    </Button>
                  </Card.Footer>
                </Card>
              </Col>
            );
          })}
        </Row>
      )}
    </div>
  );
};

export default PredictionsView;