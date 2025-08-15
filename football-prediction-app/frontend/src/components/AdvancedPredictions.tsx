import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Badge, ProgressBar, Button, Form, Spinner, Alert, Nav } from 'react-bootstrap';
import axios from 'axios';
import './AdvancedPredictions.css';

interface AdvancedPrediction {
  fixture_id: number;
  fixture: {
    home_team: string;
    away_team: string;
    date: string;
    league: string;
    venue: string;
  };
  probabilities: {
    home_win: number;
    draw: number;
    away_win: number;
  };
  goals: {
    predicted_home: number;
    predicted_away: number;
    total_expected: number;
  };
  markets: {
    btts: {
      yes: number;
      no: number;
    };
    over_under: {
      over_25: number;
      under_25: number;
      over_35: number;
      under_35: number;
    };
  };
  confidence_score: number;
  prediction_summary: string;
  value_bets: Array<{
    type: string;
    selection: string;
    probability: number;
    confidence: string;
  }>;
  factors_breakdown?: {
    [key: string]: {
      home: number;
      away: number;
      weight: number;
    };
  };
}

interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

const AdvancedPredictions: React.FC = () => {
  const [predictions, setPredictions] = useState<AdvancedPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0
  });
  
  // Filters
  const [dateFrom, setDateFrom] = useState(new Date().toISOString().split('T')[0]);
  const [dateTo, setDateTo] = useState(new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  const [minConfidence, setMinConfidence] = useState(60);
  const [leagueId, setLeagueId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'all' | 'value-bets'>('all');

  const fetchPredictions = async (page: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = {
        date_from: dateFrom,
        date_to: dateTo,
        min_confidence: minConfidence,
        page,
        per_page: 10
      };
      
      if (leagueId) {
        params.league_id = leagueId;
      }
      
      const endpoint = viewMode === 'value-bets' 
        ? `${process.env.REACT_APP_API_URL}/api/v1/predictions/advanced/value-bets`
        : `${process.env.REACT_APP_API_URL}/api/v1/predictions/advanced`;
      
      const response = await axios.get(endpoint, { params });
      
      if (viewMode === 'value-bets') {
        // Transform value bets response to match predictions format
        const valueBets = response.data.value_bets.map((vb: any) => ({
          fixture_id: vb.fixture_id,
          fixture: vb.fixture,
          probabilities: {
            home_win: 0,
            draw: 0,
            away_win: 0
          },
          goals: {
            predicted_home: 0,
            predicted_away: 0,
            total_expected: 0
          },
          markets: {
            btts: { yes: 0, no: 0 },
            over_under: {
              over_25: 0,
              under_25: 0,
              over_35: 0,
              under_35: 0
            }
          },
          confidence_score: vb.confidence_score,
          prediction_summary: `${vb.bet.type}: ${vb.bet.selection} (${vb.bet.probability}%)`,
          value_bets: [vb.bet]
        }));
        setPredictions(valueBets);
        setPagination({
          page: 1,
          per_page: valueBets.length,
          total: valueBets.length,
          total_pages: 1
        });
      } else {
        setPredictions(response.data.predictions);
        setPagination(response.data.pagination);
      }
    } catch (err) {
      console.error('Error fetching predictions:', err);
      setError('Failed to load predictions. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [dateFrom, dateTo, minConfidence, leagueId, viewMode]);

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 80) return <Badge bg="success">Very High Confidence</Badge>;
    if (confidence >= 70) return <Badge bg="primary">High Confidence</Badge>;
    if (confidence >= 60) return <Badge bg="info">Good Confidence</Badge>;
    return <Badge bg="warning">Moderate Confidence</Badge>;
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 70) return 'success';
    if (probability >= 60) return 'primary';
    if (probability >= 50) return 'info';
    if (probability >= 40) return 'warning';
    return 'secondary';
  };

  const getMatchResultPrediction = (probs: AdvancedPrediction['probabilities']) => {
    const max = Math.max(probs.home_win, probs.draw, probs.away_win);
    if (max === probs.home_win) return { result: 'Home Win', probability: probs.home_win };
    if (max === probs.draw) return { result: 'Draw', probability: probs.draw };
    return { result: 'Away Win', probability: probs.away_win };
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

  const renderFactorsBreakdown = (factors?: AdvancedPrediction['factors_breakdown']) => {
    if (!factors) return null;

    return (
      <div className="factors-breakdown mt-3">
        <h6>Prediction Factors</h6>
        {Object.entries(factors).map(([factor, data]) => (
          <div key={factor} className="factor-item mb-2">
            <small className="text-muted">{factor.replace(/_/g, ' ').toUpperCase()} ({(data.weight * 100).toFixed(0)}%)</small>
            <div className="d-flex justify-content-between">
              <div className="text-start">Home: {(data.home * 10).toFixed(1)}/10</div>
              <div className="text-end">Away: {(data.away * 10).toFixed(1)}/10</div>
            </div>
            <ProgressBar className="factor-bar">
              <ProgressBar
                variant="primary"
                now={data.home * 100}
                key={1}
              />
              <ProgressBar
                variant="danger"
                now={data.away * 100}
                key={2}
              />
            </ProgressBar>
          </div>
        ))}
      </div>
    );
  };

  if (loading && predictions.length === 0) {
    return (
      <Container className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading advanced predictions...</p>
      </Container>
    );
  }

  return (
    <Container className="advanced-predictions-container py-4">
      <Row className="mb-4">
        <Col>
          <h2>AI-Powered Football Predictions</h2>
          <p className="text-muted">
            Advanced predictions using multiple data sources including form, head-to-head, injuries, and more.
          </p>
        </Col>
      </Row>

      {/* Filters */}
      <Card className="mb-4">
        <Card.Body>
          <Row className="g-3">
            <Col md={3}>
              <Form.Group>
                <Form.Label>From Date</Form.Label>
                <Form.Control
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group>
                <Form.Label>To Date</Form.Label>
                <Form.Control
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group>
                <Form.Label>Min Confidence (%)</Form.Label>
                <Form.Control
                  type="number"
                  min="0"
                  max="100"
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(Number(e.target.value))}
                />
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group>
                <Form.Label>League</Form.Label>
                <Form.Select
                  value={leagueId || ''}
                  onChange={(e) => setLeagueId(e.target.value ? Number(e.target.value) : null)}
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
        </Card.Body>
      </Card>

      {/* View Mode Tabs */}
      <Nav variant="tabs" className="mb-4">
        <Nav.Item>
          <Nav.Link
            active={viewMode === 'all'}
            onClick={() => setViewMode('all')}
          >
            All Predictions
          </Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link
            active={viewMode === 'value-bets'}
            onClick={() => setViewMode('value-bets')}
          >
            Value Bets Only
          </Nav.Link>
        </Nav.Item>
      </Nav>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Predictions List */}
      {predictions.length === 0 ? (
        <Alert variant="info">
          No predictions found for the selected criteria. Try adjusting your filters.
        </Alert>
      ) : (
        <>
          <Row>
            {predictions.map((prediction) => {
              const mainPrediction = viewMode === 'all' ? getMatchResultPrediction(prediction.probabilities) : null;
              
              return (
                <Col key={prediction.fixture_id} lg={6} className="mb-4">
                  <Card className="prediction-card h-100 shadow-sm">
                    <Card.Header className="prediction-header">
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <h5 className="mb-1">
                            {prediction.fixture.home_team} vs {prediction.fixture.away_team}
                          </h5>
                          <small className="text-muted">
                            {prediction.fixture.league} • {formatDate(prediction.fixture.date)}
                          </small>
                          {prediction.fixture.venue && (
                            <small className="text-muted d-block">{prediction.fixture.venue}</small>
                          )}
                        </div>
                        <div className="text-end">
                          {getConfidenceBadge(prediction.confidence_score)}
                          <div className="confidence-score mt-1">
                            {prediction.confidence_score.toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    </Card.Header>
                    
                    <Card.Body>
                      {/* Prediction Summary */}
                      <Alert variant="light" className="prediction-summary">
                        {prediction.prediction_summary}
                      </Alert>

                      {/* Match Result Probabilities */}
                      {viewMode === 'all' && mainPrediction && (
                        <div className="match-result-section mb-4">
                          <h6>Match Result Probabilities</h6>
                          <div className="probability-bars">
                            <div className="prob-item mb-2">
                              <div className="d-flex justify-content-between mb-1">
                                <span>Home Win</span>
                                <span>{prediction.probabilities.home_win.toFixed(1)}%</span>
                              </div>
                              <ProgressBar 
                                now={prediction.probabilities.home_win} 
                                variant={getProbabilityColor(prediction.probabilities.home_win)}
                              />
                            </div>
                            <div className="prob-item mb-2">
                              <div className="d-flex justify-content-between mb-1">
                                <span>Draw</span>
                                <span>{prediction.probabilities.draw.toFixed(1)}%</span>
                              </div>
                              <ProgressBar 
                                now={prediction.probabilities.draw} 
                                variant={getProbabilityColor(prediction.probabilities.draw)}
                              />
                            </div>
                            <div className="prob-item mb-2">
                              <div className="d-flex justify-content-between mb-1">
                                <span>Away Win</span>
                                <span>{prediction.probabilities.away_win.toFixed(1)}%</span>
                              </div>
                              <ProgressBar 
                                now={prediction.probabilities.away_win} 
                                variant={getProbabilityColor(prediction.probabilities.away_win)}
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Goals Prediction */}
                      {viewMode === 'all' && prediction.goals.total_expected > 0 && (
                        <div className="goals-section mb-4">
                          <h6>Goals Prediction</h6>
                          <Row>
                            <Col xs={6}>
                              <div className="text-center">
                                <div className="predicted-score">{prediction.goals.predicted_home.toFixed(1)}</div>
                                <small className="text-muted">{prediction.fixture.home_team}</small>
                              </div>
                            </Col>
                            <Col xs={6}>
                              <div className="text-center">
                                <div className="predicted-score">{prediction.goals.predicted_away.toFixed(1)}</div>
                                <small className="text-muted">{prediction.fixture.away_team}</small>
                              </div>
                            </Col>
                          </Row>
                          <div className="text-center mt-2">
                            <Badge bg="secondary">
                              Total Goals Expected: {prediction.goals.total_expected.toFixed(1)}
                            </Badge>
                          </div>
                        </div>
                      )}

                      {/* Markets */}
                      {viewMode === 'all' && (
                        <div className="markets-section mb-4">
                          <h6>Market Predictions</h6>
                          <Row>
                            <Col xs={6}>
                              <div className="market-item">
                                <small>Over 2.5 Goals</small>
                                <ProgressBar 
                                  now={prediction.markets.over_under.over_25} 
                                  label={`${prediction.markets.over_under.over_25.toFixed(1)}%`}
                                  variant={getProbabilityColor(prediction.markets.over_under.over_25)}
                                />
                              </div>
                            </Col>
                            <Col xs={6}>
                              <div className="market-item">
                                <small>BTTS Yes</small>
                                <ProgressBar 
                                  now={prediction.markets.btts.yes} 
                                  label={`${prediction.markets.btts.yes.toFixed(1)}%`}
                                  variant={getProbabilityColor(prediction.markets.btts.yes)}
                                />
                              </div>
                            </Col>
                          </Row>
                        </div>
                      )}

                      {/* Value Bets */}
                      {prediction.value_bets.length > 0 && (
                        <div className="value-bets-section">
                          <h6>
                            {viewMode === 'value-bets' ? 'Value Bet Details' : 'Recommended Bets'}
                          </h6>
                          {prediction.value_bets.map((bet, index) => (
                            <Badge 
                              key={index} 
                              bg={bet.confidence === 'high' ? 'success' : 'primary'} 
                              className="me-2 mb-2"
                            >
                              {bet.type}: {bet.selection} ({bet.probability}%)
                            </Badge>
                          ))}
                        </div>
                      )}

                      {/* Factors Breakdown (optional) */}
                      {viewMode === 'all' && prediction.factors_breakdown && (
                        <div className="mt-3">
                          {renderFactorsBreakdown(prediction.factors_breakdown)}
                        </div>
                      )}
                    </Card.Body>
                  </Card>
                </Col>
              );
            })}
          </Row>

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="d-flex justify-content-center mt-4">
              <Button
                variant="outline-primary"
                onClick={() => fetchPredictions(pagination.page - 1)}
                disabled={pagination.page === 1}
                className="me-2"
              >
                Previous
              </Button>
              <span className="align-self-center mx-3">
                Page {pagination.page} of {pagination.total_pages}
              </span>
              <Button
                variant="outline-primary"
                onClick={() => fetchPredictions(pagination.page + 1)}
                disabled={pagination.page === pagination.total_pages}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </Container>
  );
};

export default AdvancedPredictions;