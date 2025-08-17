import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Row, Col, Table, Alert, Form, Button } from 'react-bootstrap';
import { DollarSign, TrendingUp, AlertTriangle, Filter, ChevronUp } from 'lucide-react';
import axios from '../services/api';
import './ValueBets.css';

interface ValueBet {
  fixture_id: number;
  fixture_name: string;
  market: string;
  selection: string;
  predicted_probability: number;
  bookmaker_odds: number;
  value_percentage: number;
  recommended_stake: number;
}

const ValueBets: React.FC = () => {
  const [valueBets, setValueBets] = useState<ValueBet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [minValue, setMinValue] = useState(5);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  const fetchValueBets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        min_value: minValue.toString(),
        date: selectedDate,
      });

      const response = await axios.get(
        `/api/sportmonks/value-bets?${params}`
      );
      
      setValueBets(response.data.value_bets);
      setError(null);
    } catch (err) {
      console.error('Error fetching value bets:', err);
      setError('Failed to fetch value bets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchValueBets();
  }, [minValue, selectedDate]);

  const getValueBadgeColor = (value: number) => {
    if (value >= 20) return 'success';
    if (value >= 10) return 'warning';
    return 'info';
  };

  const calculatePotentialProfit = (stake: number, odds: number) => {
    return (stake * (odds - 1)).toFixed(2);
  };

  const getMarketIcon = (market: string) => {
    const marketIcons: Record<string, string> = {
      '1X2': '⚽',
      'Over/Under': '📊',
      'BTTS': '🥅',
      'Asian Handicap': '📈',
      'Correct Score': '🎯',
    };
    return marketIcons[market] || '📌';
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="success" />
        <p className="mt-3">Analyzing value betting opportunities...</p>
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

  return (
    <div className="value-bets-container">
      <div className="value-bets-header mb-4">
        <Row className="align-items-center">
          <Col md={6}>
            <h3 className="mb-0">
              <DollarSign className="me-2" size={24} />
              Value Bets
            </h3>
            <p className="text-muted mb-0">High-value betting opportunities identified by AI</p>
          </Col>
          <Col md={6}>
            <Row className="g-2">
              <Col sm={6}>
                <Form.Group>
                  <Form.Label className="small">
                    <Filter size={14} className="me-1" />
                    Minimum Value
                  </Form.Label>
                  <Form.Select 
                    value={minValue} 
                    onChange={(e) => setMinValue(Number(e.target.value))}
                    size="sm"
                  >
                    <option value={5}>5% or higher</option>
                    <option value={10}>10% or higher</option>
                    <option value={15}>15% or higher</option>
                    <option value={20}>20% or higher</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col sm={6}>
                <Form.Group>
                  <Form.Label className="small">Date</Form.Label>
                  <Form.Control 
                    type="date" 
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    size="sm"
                  />
                </Form.Group>
              </Col>
            </Row>
          </Col>
        </Row>
      </div>

      {valueBets.length === 0 ? (
        <Card className="text-center py-5">
          <Card.Body>
            <DollarSign size={48} className="text-muted mb-3" />
            <h5>No Value Bets Found</h5>
            <p className="text-muted">
              No bets meeting your criteria were found. Try adjusting the filters.
            </p>
          </Card.Body>
        </Card>
      ) : (
        <>
          <Alert variant="info" className="mb-4">
            <strong>💡 Tip:</strong> Value bets occur when the predicted probability is higher than 
            the bookmaker's implied probability. Higher value percentages indicate better opportunities.
          </Alert>

          <Card className="value-bets-card shadow-sm">
            <Card.Body className="p-0">
              <div className="table-responsive">
                <Table hover className="mb-0">
                  <thead className="value-bets-header-table">
                    <tr>
                      <th>Match</th>
                      <th>Market</th>
                      <th>Selection</th>
                      <th className="text-center">Predicted %</th>
                      <th className="text-center">Odds</th>
                      <th className="text-center">Value</th>
                      <th className="text-center">Stake</th>
                      <th className="text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {valueBets.map((bet, index) => (
                      <tr key={index} className="value-bet-row">
                        <td>
                          <div className="match-info">
                            <div className="match-name">{bet.fixture_name}</div>
                          </div>
                        </td>
                        <td>
                          <span className="market-badge">
                            {getMarketIcon(bet.market)} {bet.market}
                          </span>
                        </td>
                        <td>
                          <Badge bg="secondary" className="selection-badge">
                            {bet.selection}
                          </Badge>
                        </td>
                        <td className="text-center">
                          <div className="probability">
                            {bet.predicted_probability.toFixed(1)}%
                          </div>
                        </td>
                        <td className="text-center">
                          <div className="odds">
                            {bet.bookmaker_odds.toFixed(2)}
                          </div>
                        </td>
                        <td className="text-center">
                          <Badge 
                            bg={getValueBadgeColor(bet.value_percentage)} 
                            className="value-badge"
                          >
                            <ChevronUp size={14} />
                            {bet.value_percentage.toFixed(1)}%
                          </Badge>
                        </td>
                        <td className="text-center">
                          <div className="stake-suggestion">
                            {(bet.recommended_stake * 100).toFixed(0)}%
                          </div>
                          <small className="text-muted">of bankroll</small>
                        </td>
                        <td className="text-center">
                          <Button 
                            variant="outline-success" 
                            size="sm"
                            className="bet-action-btn"
                          >
                            <TrendingUp size={14} className="me-1" />
                            Details
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>

          <Row className="mt-4">
            <Col md={4}>
              <Card className="info-card text-center">
                <Card.Body>
                  <h2 className="text-success mb-1">{valueBets.length}</h2>
                  <p className="text-muted mb-0">Value Bets Found</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={4}>
              <Card className="info-card text-center">
                <Card.Body>
                  <h2 className="text-warning mb-1">
                    {(valueBets.reduce((sum, bet) => sum + bet.value_percentage, 0) / valueBets.length).toFixed(1)}%
                  </h2>
                  <p className="text-muted mb-0">Average Value</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={4}>
              <Card className="info-card text-center">
                <Card.Body>
                  <h2 className="text-info mb-1">
                    {Math.max(...valueBets.map(bet => bet.value_percentage)).toFixed(1)}%
                  </h2>
                  <p className="text-muted mb-0">Best Value</p>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default ValueBets;