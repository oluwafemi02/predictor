import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Row, Col, Alert, Form, Button, Tab, Nav } from 'react-bootstrap';
import { DollarSign, TrendingUp, AlertTriangle, Calendar, Target } from 'lucide-react';
import axios from '../services/api';
import PredictionDetails from './PredictionDetails';
import OddsDisplay from './OddsDisplay';
import './EnhancedValueBets.css';

interface Fixture {
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
  predictions?: any;
  prediction_confidence?: string;
}

const EnhancedValueBets: React.FC = () => {
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedLeague, setSelectedLeague] = useState<string>('8'); // EPL default

  useEffect(() => {
    fetchFixturesWithPredictions();
  }, [selectedDate, selectedLeague]);

  const fetchFixturesWithPredictions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        days_back: '0',
        days_ahead: '7',
        league_id: selectedLeague,
        predictions: 'true'
      });

      const response = await axios.get(
        `/api/sportmonks/fixtures/all?${params}`,
        {
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );
      
      if (response.data && response.data.fixtures) {
        const allFixtures = [
          ...response.data.fixtures.today,
          ...response.data.fixtures.upcoming
        ].filter(f => f.predictions && f.predictions.match_winner);
        
        setFixtures(allFixtures);
      } else {
        setFixtures([]);
      }
    } catch (err) {
      console.error('Error fetching fixtures:', err);
      setError('Failed to fetch fixtures with predictions');
    } finally {
      setLoading(false);
    }
  };

  const getValueBets = () => {
    // Find fixtures where predictions significantly differ from odds
    return fixtures.filter(fixture => {
      if (!fixture.predictions?.match_winner) return false;
      
      const pred = fixture.predictions.match_winner;
      const maxProb = Math.max(pred.home_win, pred.draw, pred.away_win);
      
      // Consider it a value bet if any outcome has >60% probability
      return maxProb > 60;
    });
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="success" />
        <p className="mt-3">Loading predictions and odds...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        <AlertTriangle className="me-2" />
        <strong>Error:</strong> {error}
      </Alert>
    );
  }

  const valueBets = getValueBets();

  return (
    <div className="enhanced-value-bets">
      <div className="mb-4">
        <Row className="align-items-center">
          <Col md={6}>
            <h3 className="mb-0">
              <DollarSign className="me-2" size={24} />
              Enhanced Predictions & Odds
            </h3>
            <p className="text-muted mb-0">AI-powered predictions with live odds comparison</p>
          </Col>
          <Col md={6}>
            <Row>
              <Col md={6}>
                <Form.Group>
                  <Form.Label>League</Form.Label>
                  <Form.Select 
                    value={selectedLeague} 
                    onChange={(e) => setSelectedLeague(e.target.value)}
                  >
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

      {valueBets.length > 0 && (
        <Alert variant="success" className="mb-4">
          <Target className="me-2" />
          <strong>{valueBets.length} High Confidence Predictions Found!</strong> 
          <span className="ms-2">Fixtures with &gt;60% win probability</span>
        </Alert>
      )}

      <Tab.Container defaultActiveKey="all">
        <Nav variant="pills" className="mb-4">
          <Nav.Item>
            <Nav.Link eventKey="all">
              All Fixtures ({fixtures.length})
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="value">
              <TrendingUp size={16} className="me-1" />
              Value Bets ({valueBets.length})
            </Nav.Link>
          </Nav.Item>
        </Nav>

        <Tab.Content>
          <Tab.Pane eventKey="all">
            <Row>
              {fixtures.map((fixture) => (
                <Col key={fixture.id} lg={6} className="mb-4">
                  <Card className="fixture-prediction-card h-100">
                    <Card.Header>
                      <div className="d-flex justify-content-between align-items-center">
                        <div>
                          <h5 className="mb-0">
                            {fixture.home_team.name} vs {fixture.away_team.name}
                          </h5>
                          <small className="text-muted">
                            <Calendar size={14} className="me-1" />
                            {new Date(fixture.date).toLocaleDateString()} - {fixture.league.name}
                          </small>
                        </div>
                        {fixture.prediction_confidence && (
                          <Badge 
                            bg={
                              fixture.prediction_confidence === 'high' ? 'success' : 
                              fixture.prediction_confidence === 'medium' ? 'warning' : 'danger'
                            }
                          >
                            {fixture.prediction_confidence.toUpperCase()}
                          </Badge>
                        )}
                      </div>
                    </Card.Header>
                    <Card.Body>
                      <PredictionDetails
                        predictions={fixture.predictions || {}}
                        confidence={fixture.prediction_confidence || 'medium'}
                        homeTeam={fixture.home_team.name}
                        awayTeam={fixture.away_team.name}
                      />
                      
                      <hr className="my-4" />
                      
                      <h6 className="mb-3">
                        <DollarSign size={16} className="me-1" />
                        Live Odds Comparison
                      </h6>
                      <OddsDisplay 
                        fixtureId={fixture.id} 
                        showProbabilities={true}
                      />
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </Tab.Pane>
          
          <Tab.Pane eventKey="value">
            <Row>
              {valueBets.map((fixture) => (
                <Col key={fixture.id} lg={6} className="mb-4">
                  <Card className="fixture-prediction-card value-bet-card h-100">
                    <Card.Header className="bg-success text-white">
                      <div className="d-flex justify-content-between align-items-center">
                        <div>
                          <h5 className="mb-0">
                            {fixture.home_team.name} vs {fixture.away_team.name}
                          </h5>
                          <small>
                            <Calendar size={14} className="me-1" />
                            {new Date(fixture.date).toLocaleDateString()} - {fixture.league.name}
                          </small>
                        </div>
                        <Badge bg="light" text="dark">
                          VALUE BET
                        </Badge>
                      </div>
                    </Card.Header>
                    <Card.Body>
                      <PredictionDetails
                        predictions={fixture.predictions || {}}
                        confidence={fixture.prediction_confidence || 'high'}
                        homeTeam={fixture.home_team.name}
                        awayTeam={fixture.away_team.name}
                      />
                      
                      <hr className="my-4" />
                      
                      <h6 className="mb-3">
                        <DollarSign size={16} className="me-1" />
                        Live Odds - Compare with Predictions
                      </h6>
                      <OddsDisplay 
                        fixtureId={fixture.id} 
                        showProbabilities={true}
                      />
                    </Card.Body>
                  </Card>
                </Col>
              ))}
              {valueBets.length === 0 && (
                <Col>
                  <Alert variant="info">
                    No high-confidence value bets found for the selected criteria.
                  </Alert>
                </Col>
              )}
            </Row>
          </Tab.Pane>
        </Tab.Content>
      </Tab.Container>
    </div>
  );
};

export default EnhancedValueBets;