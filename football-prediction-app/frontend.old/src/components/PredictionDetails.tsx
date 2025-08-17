import React from 'react';
import { Card, Row, Col, Badge, ProgressBar, Table } from 'react-bootstrap';
import { TrendingUp, Target, Users, BarChart3, AlertCircle, Zap } from 'lucide-react';
import './PredictionDetails.css';

interface PredictionDetailsProps {
  predictions: {
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
  confidence?: string;
  homeTeam: string;
  awayTeam: string;
}

const PredictionDetails: React.FC<PredictionDetailsProps> = ({ 
  predictions, 
  confidence = 'medium',
  homeTeam,
  awayTeam 
}) => {
  const getConfidenceBadge = () => {
    const variants: Record<string, string> = {
      high: 'success',
      medium: 'warning',
      low: 'danger'
    };
    return (
      <Badge bg={variants[confidence]} className="confidence-badge">
        <Zap size={14} className="me-1" />
        {confidence.toUpperCase()} Confidence
      </Badge>
    );
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 70) return 'success';
    if (probability >= 50) return 'warning';
    return 'info';
  };

  const formatProbability = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  if (!predictions || Object.keys(predictions).length === 0) {
    return (
      <div className="text-center py-4">
        <AlertCircle size={48} className="text-muted mb-2" />
        <p className="text-muted">No predictions available</p>
      </div>
    );
  }

  return (
    <div className="prediction-details">
      <div className="text-end mb-3">
        {getConfidenceBadge()}
      </div>

      {/* Match Winner */}
      {predictions.match_winner && (
        <Card className="mb-3 prediction-card">
          <Card.Header>
            <h6 className="mb-0">
              <Target size={18} className="me-2" />
              Match Result
            </h6>
          </Card.Header>
          <Card.Body>
            <Row>
              <Col xs={4}>
                <div className="text-center">
                  <small className="text-muted">{homeTeam}</small>
                  <h4 className="mb-1">{formatProbability(predictions.match_winner.home_win)}</h4>
                  <ProgressBar 
                    now={predictions.match_winner.home_win} 
                    variant={getProbabilityColor(predictions.match_winner.home_win)}
                    style={{ height: '8px' }}
                  />
                </div>
              </Col>
              <Col xs={4}>
                <div className="text-center">
                  <small className="text-muted">Draw</small>
                  <h4 className="mb-1">{formatProbability(predictions.match_winner.draw)}</h4>
                  <ProgressBar 
                    now={predictions.match_winner.draw} 
                    variant={getProbabilityColor(predictions.match_winner.draw)}
                    style={{ height: '8px' }}
                  />
                </div>
              </Col>
              <Col xs={4}>
                <div className="text-center">
                  <small className="text-muted">{awayTeam}</small>
                  <h4 className="mb-1">{formatProbability(predictions.match_winner.away_win)}</h4>
                  <ProgressBar 
                    now={predictions.match_winner.away_win} 
                    variant={getProbabilityColor(predictions.match_winner.away_win)}
                    style={{ height: '8px' }}
                  />
                </div>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}

      {/* Goals Over/Under */}
      {predictions.goals && (
        <Card className="mb-3 prediction-card">
          <Card.Header>
            <h6 className="mb-0">
              <TrendingUp size={18} className="me-2" />
              Total Goals
            </h6>
          </Card.Header>
          <Card.Body>
            <Table size="sm" className="mb-0">
              <tbody>
                <tr>
                  <td>Over 1.5</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.goals.over_15)}>
                      {formatProbability(predictions.goals.over_15)}
                    </Badge>
                  </td>
                  <td>Under 1.5</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.goals.under_15)}>
                      {formatProbability(predictions.goals.under_15)}
                    </Badge>
                  </td>
                </tr>
                <tr>
                  <td>Over 2.5</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.goals.over_25)}>
                      {formatProbability(predictions.goals.over_25)}
                    </Badge>
                  </td>
                  <td>Under 2.5</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.goals.under_25)}>
                      {formatProbability(predictions.goals.under_25)}
                    </Badge>
                  </td>
                </tr>
                <tr>
                  <td>Over 3.5</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.goals.over_35)}>
                      {formatProbability(predictions.goals.over_35)}
                    </Badge>
                  </td>
                  <td>Under 3.5</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.goals.under_35)}>
                      {formatProbability(predictions.goals.under_35)}
                    </Badge>
                  </td>
                </tr>
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}

      {/* BTTS */}
      {predictions.btts && (
        <Card className="mb-3 prediction-card">
          <Card.Header>
            <h6 className="mb-0">
              <Users size={18} className="me-2" />
              Both Teams to Score
            </h6>
          </Card.Header>
          <Card.Body>
            <Row>
              <Col xs={6}>
                <div className="text-center">
                  <h5 className="mb-1">Yes</h5>
                  <Badge bg={getProbabilityColor(predictions.btts.yes)} className="fs-6">
                    {formatProbability(predictions.btts.yes)}
                  </Badge>
                </div>
              </Col>
              <Col xs={6}>
                <div className="text-center">
                  <h5 className="mb-1">No</h5>
                  <Badge bg={getProbabilityColor(predictions.btts.no)} className="fs-6">
                    {formatProbability(predictions.btts.no)}
                  </Badge>
                </div>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}

      {/* Correct Score */}
      {predictions.correct_scores && predictions.correct_scores.length > 0 && (
        <Card className="mb-3 prediction-card">
          <Card.Header>
            <h6 className="mb-0">
              <BarChart3 size={18} className="me-2" />
              Most Likely Scores
            </h6>
          </Card.Header>
          <Card.Body>
            <div className="correct-scores-grid">
              {predictions.correct_scores.slice(0, 6).map((score, idx) => (
                <div key={idx} className="score-prediction">
                  <Badge 
                    bg={idx === 0 ? 'success' : idx < 3 ? 'primary' : 'secondary'}
                    className="score-badge"
                  >
                    {score.score}
                  </Badge>
                  <small className="text-muted">{formatProbability(score.probability)}</small>
                </div>
              ))}
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Double Chance */}
      {predictions.double_chance && (
        <Card className="mb-3 prediction-card">
          <Card.Header>
            <h6 className="mb-0">
              <Target size={18} className="me-2" />
              Double Chance
            </h6>
          </Card.Header>
          <Card.Body>
            <Table size="sm" className="mb-0">
              <tbody>
                <tr>
                  <td>{homeTeam} or Draw</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.double_chance.home_or_draw)}>
                      {formatProbability(predictions.double_chance.home_or_draw)}
                    </Badge>
                  </td>
                </tr>
                <tr>
                  <td>{awayTeam} or Draw</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.double_chance.away_or_draw)}>
                      {formatProbability(predictions.double_chance.away_or_draw)}
                    </Badge>
                  </td>
                </tr>
                <tr>
                  <td>{homeTeam} or {awayTeam}</td>
                  <td className="text-end">
                    <Badge bg={getProbabilityColor(predictions.double_chance.home_or_away)}>
                      {formatProbability(predictions.double_chance.home_or_away)}
                    </Badge>
                  </td>
                </tr>
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default PredictionDetails;