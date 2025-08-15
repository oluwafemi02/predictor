import React, { useState, useEffect } from 'react';
import {
  Container,
  Row,
  Col,
  Card,
  Form,
  Spinner,
  Alert,
  Badge,
  Table,
  Button,
  Modal
} from 'react-bootstrap';
import axios from 'axios';
import './SquadView.css';

interface Player {
  id: number;
  name: string;
  position: string;
  number: number | null;
  nationality: string;
  age: number;
  image: string;
}

interface Team {
  id: number;
  name: string;
  short_code: string;
  logo: string;
  founded: number;
  country: string;
  venue?: {
    name: string;
    city: string;
    capacity: number;
  };
  is_mock_data?: boolean;
}

interface TeamWithSquad extends Team {
  squad: Player[];
}

const SquadView: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<TeamWithSquad | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<string>('');
  const [leagues, setLeagues] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingSquad, setLoadingSquad] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch available leagues on component mount
  useEffect(() => {
    fetchLeagues();
  }, []);

  const fetchLeagues = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/sportmonks/leagues`
      );
      setLeagues(response.data.leagues || []);
    } catch (err) {
      console.error('Error fetching leagues:', err);
    }
  };

  const fetchTeamsByLeague = async (leagueId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/sportmonks/leagues/${leagueId}/teams`
      );
      setTeams(response.data.teams || []);
    } catch (err) {
      console.error('Error fetching teams:', err);
      setError('Failed to fetch teams');
      setTeams([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeamSquad = async (teamId: number) => {
    setLoadingSquad(true);
    setError(null);
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/sportmonks/teams/${teamId}?include=squad,venue,league,stats`
      );
      console.log('Team data received:', response.data);
      
      if (response.data) {
        setSelectedTeam(response.data);
        
        // Check if squad data exists
        if (!response.data.squad || response.data.squad.length === 0) {
          console.warn('No squad data available for team:', response.data.name);
        }
        
        setShowModal(true);
      } else {
        setError('No team data received');
      }
    } catch (err: any) {
      console.error('Error fetching team squad:', err);
      let errorMessage = 'Failed to fetch squad data';
      
      if (err.response) {
        errorMessage = err.response.data?.message || err.response.data?.error || `Server error: ${err.response.status}`;
      } else if (err.request) {
        errorMessage = 'Unable to reach the server. Please check your connection.';
      } else {
        errorMessage = err.message || 'An unexpected error occurred';
      }
      
      setError(errorMessage);
    } finally {
      setLoadingSquad(false);
    }
  };

  const searchTeams = async () => {
    if (searchQuery.length < 3) {
      setError('Search query must be at least 3 characters');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/sportmonks/search/teams?q=${searchQuery}`
      );
      setTeams(response.data.teams || []);
    } catch (err) {
      console.error('Error searching teams:', err);
      setError('Failed to search teams');
      setTeams([]);
    } finally {
      setLoading(false);
    }
  };

  const handleLeagueChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const leagueId = e.target.value;
    setSelectedLeague(leagueId);
    if (leagueId) {
      fetchTeamsByLeague(leagueId);
    } else {
      setTeams([]);
    }
  };

  const groupPlayersByPosition = (players: Player[]) => {
    const grouped: { [key: string]: Player[] } = {};
    players.forEach(player => {
      if (!grouped[player.position]) {
        grouped[player.position] = [];
      }
      grouped[player.position].push(player);
    });
    return grouped;
  };

  return (
    <Container fluid className="squad-view-container">
      <h2 className="mb-4">Team Squads</h2>

      <Row className="mb-4">
        <Col md={6}>
          <Form.Group>
            <Form.Label>Select League</Form.Label>
            <Form.Select
              value={selectedLeague}
              onChange={handleLeagueChange}
              className="league-select"
            >
              <option value="">Choose a league...</option>
              {leagues.map(league => (
                <option key={league.id} value={league.id}>
                  {league.name} ({league.country})
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
        <Col md={6}>
          <Form.Group>
            <Form.Label>Search Teams</Form.Label>
            <div className="d-flex">
              <Form.Control
                type="text"
                placeholder="Search by team name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchTeams()}
              />
              <Button
                variant="primary"
                onClick={searchTeams}
                className="ms-2"
                disabled={loading}
              >
                Search
              </Button>
            </div>
          </Form.Group>
        </Col>
      </Row>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading teams...</span>
          </Spinner>
        </div>
      ) : (
        <Row>
          {teams.map(team => (
            <Col key={team.id} md={6} lg={4} xl={3} className="mb-4">
              <Card className="team-card h-100">
                <Card.Body className="d-flex flex-column">
                  <div className="team-header mb-3">
                    {team.logo && (
                      <img
                        src={team.logo}
                        alt={team.name}
                        className="team-logo"
                      />
                    )}
                    <h5 className="team-name">{team.name}</h5>
                    {team.short_code && (
                      <Badge bg="secondary">{team.short_code}</Badge>
                    )}
                  </div>
                  <div className="team-info">
                    {team.country && <p className="mb-1">Country: {team.country}</p>}
                    {team.founded && <p className="mb-1">Founded: {team.founded}</p>}
                    {team.venue && (
                      <p className="mb-1">
                        Stadium: {team.venue.name} ({team.venue.capacity?.toLocaleString()})
                      </p>
                    )}
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    className="mt-auto"
                    onClick={() => fetchTeamSquad(team.id)}
                    disabled={loadingSquad}
                  >
                    View Squad
                  </Button>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {teams.length === 0 && !loading && selectedLeague && (
        <Alert variant="info">
          No teams found for the selected league.
        </Alert>
      )}

      {/* Squad Modal */}
      <Modal
        show={showModal}
        onHide={() => setShowModal(false)}
        size="lg"
        scrollable
      >
        <Modal.Header closeButton>
          <Modal.Title>
            {selectedTeam && (
              <div className="d-flex align-items-center">
                {selectedTeam.logo && (
                  <img
                    src={selectedTeam.logo}
                    alt={selectedTeam.name}
                    className="squad-modal-logo me-3"
                  />
                )}
                <span>{selectedTeam.name} - Squad</span>
              </div>
            )}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {loadingSquad ? (
            <div className="text-center py-5">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading squad...</span>
              </Spinner>
            </div>
          ) : selectedTeam && selectedTeam.squad && selectedTeam.squad.length > 0 ? (
            <>
              {Object.entries(groupPlayersByPosition(selectedTeam.squad)).map(
                ([position, players]) => (
                  <div key={position} className="position-group mb-4">
                    <h5 className="position-title">{position}</h5>
                    <Table striped bordered hover size="sm">
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Name</th>
                          <th>Age</th>
                          <th>Nationality</th>
                        </tr>
                      </thead>
                      <tbody>
                        {players.map(player => (
                          <tr key={player.id}>
                            <td>{player.number || '-'}</td>
                            <td className="d-flex align-items-center">
                              {player.image && (
                                <img
                                  src={player.image}
                                  alt={player.name}
                                  className="player-image me-2"
                                />
                              )}
                              {player.name}
                            </td>
                            <td>{player.age || '-'}</td>
                            <td>{player.nationality || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                )
              )}
            </>
          ) : selectedTeam ? (
            <Alert variant="info">
              No squad data available for this team.
              {selectedTeam.is_mock_data && (
                <p className="mt-2 mb-0 small">
                  Note: Using mock data. Configure SportMonks API key for real data.
                </p>
              )}
            </Alert>
          ) : (
            <Alert variant="warning">
              Unable to load team data.
            </Alert>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default SquadView;