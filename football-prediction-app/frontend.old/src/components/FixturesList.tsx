import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Row, Col, Nav, Tab } from 'react-bootstrap';
import { Calendar, Clock, MapPin, AlertCircle } from 'lucide-react';
import axios from '../services/api';
import './FixturesList.css';

interface Fixture {
  id: number;
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
  scores?: {
    localteam_score: number;
    visitorteam_score: number;
  };
  venue?: {
    name: string;
    city: string;
  };
}

interface AllFixtures {
  past: Fixture[];
  today: Fixture[];
  upcoming: Fixture[];
}

const FixturesList: React.FC = () => {
  const [fixtures, setFixtures] = useState<AllFixtures>({ past: [], today: [], upcoming: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFixtures();
  }, []);

  const fetchFixtures = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `/api/sportmonks/fixtures/all?days_back=7&days_ahead=7&league_id=8`,
        {
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        }
      );
      
      if (response.data && response.data.fixtures) {
        setFixtures(response.data.fixtures);
      } else {
        setError('No fixtures data received');
      }
    } catch (err: any) {
      console.error('Error fetching fixtures:', err);
      setError('Failed to fetch fixtures');
    } finally {
      setLoading(false);
    }
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

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading fixtures...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        <AlertCircle className="me-2" />
        {error}
      </div>
    );
  }

  const totalFixtures = fixtures.past.length + fixtures.today.length + fixtures.upcoming.length;

  return (
    <div className="fixtures-list-container">
      <h4 className="mb-4">
        <Calendar className="me-2" />
        All Fixtures ({totalFixtures})
      </h4>

      <Tab.Container defaultActiveKey="upcoming">
        <Nav variant="tabs" className="mb-4">
          <Nav.Item>
            <Nav.Link eventKey="past">
              Past ({fixtures.past.length})
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="today">
              Today ({fixtures.today.length})
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="upcoming">
              Upcoming ({fixtures.upcoming.length})
            </Nav.Link>
          </Nav.Item>
        </Nav>

        <Tab.Content>
          <Tab.Pane eventKey="past">
            {fixtures.past.length === 0 ? (
              <Card className="text-center py-4">
                <Card.Body>No past fixtures found</Card.Body>
              </Card>
            ) : (
              <div className="fixtures-grid">
                {fixtures.past.map((fixture) => (
                  <Card key={fixture.id} className="fixture-card mb-3">
                    <Card.Body>
                      <div className="fixture-header">
                        <small className="text-muted">
                          <Calendar size={14} className="me-1" />
                          {formatDate(fixture.date)}
                        </small>
                        <Badge bg="secondary">{fixture.status || 'FT'}</Badge>
                      </div>
                      <div className="fixture-teams">
                        <div className="team-row">
                          <img src={fixture.home_team.logo} alt={fixture.home_team.name} className="team-logo-xs" />
                          <span className="team-name">{fixture.home_team.name}</span>
                          {fixture.scores && (
                            <span className="team-score">{fixture.scores.localteam_score}</span>
                          )}
                        </div>
                        <div className="team-row">
                          <img src={fixture.away_team.logo} alt={fixture.away_team.name} className="team-logo-xs" />
                          <span className="team-name">{fixture.away_team.name}</span>
                          {fixture.scores && (
                            <span className="team-score">{fixture.scores.visitorteam_score}</span>
                          )}
                        </div>
                      </div>
                    </Card.Body>
                  </Card>
                ))}
              </div>
            )}
          </Tab.Pane>

          <Tab.Pane eventKey="today">
            {fixtures.today.length === 0 ? (
              <Card className="text-center py-4">
                <Card.Body>No fixtures scheduled for today</Card.Body>
              </Card>
            ) : (
              <div className="fixtures-grid">
                {fixtures.today.map((fixture) => (
                  <Card key={fixture.id} className="fixture-card mb-3">
                    <Card.Body>
                      <div className="fixture-header">
                        <small className="text-muted">
                          <Clock size={14} className="me-1" />
                          {formatDate(fixture.date)}
                        </small>
                        <Badge bg="info">Today</Badge>
                      </div>
                      <div className="fixture-teams">
                        <div className="team-row">
                          <img src={fixture.home_team.logo} alt={fixture.home_team.name} className="team-logo-xs" />
                          <span className="team-name">{fixture.home_team.name}</span>
                        </div>
                        <div className="team-row">
                          <img src={fixture.away_team.logo} alt={fixture.away_team.name} className="team-logo-xs" />
                          <span className="team-name">{fixture.away_team.name}</span>
                        </div>
                      </div>
                      {fixture.venue && (
                        <div className="fixture-venue">
                          <MapPin size={14} className="me-1" />
                          <small>{fixture.venue.name}</small>
                        </div>
                      )}
                    </Card.Body>
                  </Card>
                ))}
              </div>
            )}
          </Tab.Pane>

          <Tab.Pane eventKey="upcoming">
            {fixtures.upcoming.length === 0 ? (
              <Card className="text-center py-4">
                <Card.Body>No upcoming fixtures found</Card.Body>
              </Card>
            ) : (
              <div className="fixtures-grid">
                {fixtures.upcoming.map((fixture) => (
                  <Card key={fixture.id} className="fixture-card mb-3">
                    <Card.Body>
                      <div className="fixture-header">
                        <small className="text-muted">
                          <Calendar size={14} className="me-1" />
                          {formatDate(fixture.date)}
                        </small>
                        <Badge bg="primary">Upcoming</Badge>
                      </div>
                      <div className="fixture-teams">
                        <div className="team-row">
                          <img src={fixture.home_team.logo} alt={fixture.home_team.name} className="team-logo-xs" />
                          <span className="team-name">{fixture.home_team.name}</span>
                        </div>
                        <div className="team-row">
                          <img src={fixture.away_team.logo} alt={fixture.away_team.name} className="team-logo-xs" />
                          <span className="team-name">{fixture.away_team.name}</span>
                        </div>
                      </div>
                      {fixture.venue && (
                        <div className="fixture-venue">
                          <MapPin size={14} className="me-1" />
                          <small>{fixture.venue.name}</small>
                        </div>
                      )}
                    </Card.Body>
                  </Card>
                ))}
              </div>
            )}
          </Tab.Pane>
        </Tab.Content>
      </Tab.Container>
    </div>
  );
};

export default FixturesList;