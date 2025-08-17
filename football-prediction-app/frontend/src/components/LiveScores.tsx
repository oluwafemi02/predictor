import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Row, Col, ProgressBar } from 'react-bootstrap';
import { Clock, Activity, TrendingUp } from 'lucide-react';
import axios from '../services/api';
import './LiveScores.css';

interface LiveFixture {
  id: number;
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
  scores: {
    home: number;
    away: number;
  };
  time: {
    status: string;
    minute: number;
    added_time?: number;
  };
  stats?: any[];
  events?: any[];
}

const LiveScores: React.FC = () => {
  const [fixtures, setFixtures] = useState<LiveFixture[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchLiveScores = async () => {
    try {
      const response = await axios.get('/api/sportmonks/fixtures/live');
      setFixtures(response.data.fixtures);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching live scores:', err);
      setError('Failed to fetch live scores');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveScores();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchLiveScores, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string, minute?: number) => {
    const statusMap: Record<string, { variant: string; text: string }> = {
      'LIVE': { variant: 'danger', text: `${minute}'` },
      'HT': { variant: 'warning', text: 'Half Time' },
      'FT': { variant: 'success', text: 'Full Time' },
      'ET': { variant: 'info', text: 'Extra Time' },
      'PEN': { variant: 'primary', text: 'Penalties' },
    };

    const config = statusMap[status] || { variant: 'secondary', text: status };
    
    return (
      <Badge 
        bg={config.variant} 
        className="live-badge"
        style={{ animation: status === 'LIVE' ? 'pulse 2s infinite' : 'none' }}
      >
        {config.text}
      </Badge>
    );
  };

  const getTeamLogo = (logoUrl: string | null, teamName: string) => {
    if (logoUrl) {
      return <img src={logoUrl} alt={teamName} className="team-logo" />;
    }
    return (
      <div className="team-logo-placeholder">
        {teamName.substring(0, 2).toUpperCase()}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading live scores...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        <strong>Error:</strong> {error}
      </div>
    );
  }

  if (fixtures.length === 0) {
    return (
      <Card className="shadow-sm">
        <Card.Body className="text-center py-5">
          <Activity size={48} className="text-muted mb-3" />
          <h5>No Live Matches</h5>
          <p className="text-muted">There are no live matches at the moment.</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="live-scores-container">
      <div className="live-scores-header mb-4">
        <div className="d-flex justify-content-between align-items-center">
          <h3 className="mb-0">
            <Activity className="me-2" size={24} />
            Live Scores
          </h3>
          <div className="text-muted">
            <Clock size={16} className="me-1" />
            Updated: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>

      <Row>
        {fixtures.map((fixture) => (
          <Col key={fixture.id} lg={6} className="mb-4">
            <Card className="fixture-card shadow-sm h-100">
              <Card.Header className="fixture-header">
                <div className="d-flex justify-content-between align-items-center">
                  <div className="league-info">
                    {fixture.league.logo && (
                      <img 
                        src={fixture.league.logo} 
                        alt={fixture.league.name}
                        className="league-logo me-2"
                      />
                    )}
                    <span className="league-name">{fixture.league.name}</span>
                  </div>
                  {getStatusBadge(fixture.time.status, fixture.time.minute)}
                </div>
              </Card.Header>
              
              <Card.Body>
                <div className="fixture-content">
                  <div className="teams-container">
                    <div className="team home-team">
                      {getTeamLogo(fixture.home_team.logo, fixture.home_team.name)}
                      <div className="team-name">{fixture.home_team.name}</div>
                    </div>
                    
                    <div className="score-container">
                      <div className="score">
                        <span className="home-score">{fixture.scores.home}</span>
                        <span className="score-separator">-</span>
                        <span className="away-score">{fixture.scores.away}</span>
                      </div>
                    </div>
                    
                    <div className="team away-team">
                      {getTeamLogo(fixture.away_team.logo, fixture.away_team.name)}
                      <div className="team-name">{fixture.away_team.name}</div>
                    </div>
                  </div>
                  
                  {fixture.stats && fixture.stats.length > 0 && (
                    <div className="match-stats mt-3">
                      <h6 className="text-muted mb-2">
                        <TrendingUp size={16} className="me-1" />
                        Match Stats
                      </h6>
                      {/* Add match statistics here */}
                    </div>
                  )}
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default LiveScores;