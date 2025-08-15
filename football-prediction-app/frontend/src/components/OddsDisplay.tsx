import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Row, Col, Table, Button, ButtonGroup } from 'react-bootstrap';
import { DollarSign, TrendingUp, Calendar, Users } from 'lucide-react';
import axios from 'axios';
import './OddsDisplay.css';

interface OddsData {
  id: string;
  label: string;
  value: string;
  probability: string;
  american: string;
  fractional: string;
  decimal: string;
  winning: boolean;
  updated_at: string;
}

interface BookmakerOdds {
  bookmaker_id: number;
  bookmaker_name: string;
  odds: OddsData[];
}

interface FixtureData {
  id: number;
  name: string;
  date: string;
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
}

interface OddsDisplayProps {
  fixtureId: number;
  showProbabilities?: boolean;
}

const OddsDisplay: React.FC<OddsDisplayProps> = ({ fixtureId, showProbabilities = true }) => {
  const [odds, setOdds] = useState<Record<string, BookmakerOdds>>({});
  const [fixture, setFixture] = useState<FixtureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [oddsFormat, setOddsFormat] = useState<'decimal' | 'fractional' | 'american'>('decimal');

  useEffect(() => {
    fetchOdds();
  }, [fixtureId]);

  const fetchOdds = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/sportmonks/odds/${fixtureId}?market_id=1`
      );
      
      if (response.data && response.data.odds) {
        setOdds(response.data.odds);
        setFixture(response.data.fixture);
      } else {
        setError('No odds data available');
      }
    } catch (err: any) {
      console.error('Error fetching odds:', err);
      setError('Failed to fetch odds data');
    } finally {
      setLoading(false);
    }
  };

  const getOddsValue = (odd: OddsData) => {
    switch (oddsFormat) {
      case 'fractional':
        return odd.fractional;
      case 'american':
        return odd.american;
      default:
        return odd.decimal || odd.value;
    }
  };

  const getOddsBadgeVariant = (label: string) => {
    switch (label.toLowerCase()) {
      case 'home':
        return 'primary';
      case 'draw':
        return 'warning';
      case 'away':
        return 'info';
      default:
        return 'secondary';
    }
  };

  if (loading) {
    return (
      <div className="text-center py-3">
        <Spinner animation="border" size="sm" />
        <p className="mt-2 mb-0">Loading odds...</p>
      </div>
    );
  }

  if (error || Object.keys(odds).length === 0) {
    return (
      <div className="text-center py-3">
        <p className="text-muted mb-0">No odds available</p>
      </div>
    );
  }

  return (
    <div className="odds-display">
      {fixture && (
        <div className="fixture-header mb-3">
          <Row className="align-items-center">
            <Col>
              <div className="teams-display">
                <span className="team-name">{fixture.home_team.name}</span>
                <span className="vs-text mx-2">vs</span>
                <span className="team-name">{fixture.away_team.name}</span>
              </div>
            </Col>
            <Col xs="auto">
              <ButtonGroup size="sm">
                <Button 
                  variant={oddsFormat === 'decimal' ? 'primary' : 'outline-primary'}
                  onClick={() => setOddsFormat('decimal')}
                >
                  Decimal
                </Button>
                <Button 
                  variant={oddsFormat === 'fractional' ? 'primary' : 'outline-primary'}
                  onClick={() => setOddsFormat('fractional')}
                >
                  Fractional
                </Button>
                <Button 
                  variant={oddsFormat === 'american' ? 'primary' : 'outline-primary'}
                  onClick={() => setOddsFormat('american')}
                >
                  American
                </Button>
              </ButtonGroup>
            </Col>
          </Row>
        </div>
      )}

      {Object.entries(odds).map(([bookmakerName, bookmakerData]) => (
        <Card key={bookmakerName} className="mb-3 odds-card">
          <Card.Header className="odds-header">
            <Row className="align-items-center">
              <Col>
                <h6 className="mb-0">{bookmakerName}</h6>
              </Col>
              <Col xs="auto">
                <Badge bg="secondary" className="odds-update-badge">
                  Updated: {new Date(bookmakerData.odds[0]?.updated_at || '').toLocaleTimeString()}
                </Badge>
              </Col>
            </Row>
          </Card.Header>
          <Card.Body>
            <Row>
              {bookmakerData.odds.map((odd) => (
                <Col key={odd.id} xs={12} md={4} className="mb-2">
                  <div className={`odds-item ${odd.winning ? 'winning' : ''}`}>
                    <div className="odds-label">
                      <Badge bg={getOddsBadgeVariant(odd.label)}>
                        {odd.label}
                      </Badge>
                    </div>
                    <div className="odds-value">
                      {getOddsValue(odd)}
                    </div>
                    {showProbabilities && (
                      <div className="odds-probability">
                        {odd.probability}
                      </div>
                    )}
                  </div>
                </Col>
              ))}
            </Row>
          </Card.Body>
        </Card>
      ))}
    </div>
  );
};

export default OddsDisplay;